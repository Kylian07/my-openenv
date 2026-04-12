"""
Baseline inference script for the Data Cleaning OpenEnv.

Mandatory structured stdout logs:
  [START] {"task_id": "...", "model": "...", "env_url": "..."}
  [STEP]  {"step": 1, "action": {...}, "reward": 0.05, "score": 0.10, "done": false}
  [END]   {"task_id": "...", "final_score": 0.85, "steps": 12}

Usage:
    # Windows CMD:
    set API_BASE_URL=https://router.huggingface.co/cerebras/v1
    set MODEL_NAME=llama3.1-8b
    set HF_TOKEN=hf_xxxxx
    set ENV_URL=http://localhost:7860
    python inference.py

    # Windows PowerShell:
    $env:API_BASE_URL = "https://router.huggingface.co/cerebras/v1"
    $env:MODEL_NAME   = "llama3.1-8b"
    $env:HF_TOKEN     = "hf_xxxxx"
    $env:ENV_URL      = "http://localhost:7860"
    python inference.py
"""

import os
import sys
import json
import re
import time
import requests
from openai import OpenAI


# ══════════════════════════════════════════════════════════
#  CONFIGURATION — reads from environment variables
# ══════════════════════════════════════════════════════════
API_BASE_URL = os.environ.get(
    "API_BASE_URL", "https://router.huggingface.co/cerebras/v1"
)
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3.1-8b")
API_KEY    = os.environ.get("HF_TOKEN", os.environ.get("OPENAI_API_KEY", ""))
ENV_URL    = os.environ.get("ENV_URL", "http://localhost:7860")

MAX_AGENT_STEPS = 50       # Max actions per task (well within 20 min limit)
TEMPERATURE     = 0.0      # Deterministic output
MAX_TOKENS      = 512      # Keep small for speed on low-resource machines

# The 3 required tasks
TASKS = [
    "easy_format_standardization",
    "medium_dedup_and_fill",
    "hard_full_pipeline",
]


# ══════════════════════════════════════════════════════════
#  STRUCTURED LOGGING — mandatory [START] / [STEP] / [END]
# ══════════════════════════════════════════════════════════
def log_start(task_id: str) -> None:
    """Emit the mandatory [START] log line."""
    payload = {
        "task_id":  task_id,
        "model":    MODEL_NAME,
        "env_url":  ENV_URL,
    }
    print(f"[START] {json.dumps(payload)}", flush=True)


def log_step(step: int, action: dict, reward: float, score: float,
             done: bool, message: str = "") -> None:
    """Emit a mandatory [STEP] log line."""
    payload = {
        "step":    step,
        "action":  action,
        "reward":  round(reward, 4),
        "score":   round(score, 4),
        "done":    done,
        "message": message,
    }
    print(f"[STEP] {json.dumps(payload)}", flush=True)


def log_end(task_id: str, final_score: float, steps: int) -> None:
    """Emit the mandatory [END] log line."""
    payload = {
        "task_id":     task_id,
        "final_score": round(final_score, 4),
        "steps":       steps,
    }
    print(f"[END] {json.dumps(payload)}", flush=True)


# ══════════════════════════════════════════════════════════
#  ENVIRONMENT API HELPERS
# ══════════════════════════════════════════════════════════
def env_reset(task_id: str) -> dict:
    """Call the environment's /reset endpoint."""
    resp = requests.post(
        f"{ENV_URL}/reset",
        json={"task_id": task_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def env_step(action: dict) -> dict:
    """Call the environment's /step endpoint."""
    resp = requests.post(
        f"{ENV_URL}/step",
        json={"action": action},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def wait_for_env(max_attempts: int = 20, delay: int = 3) -> bool:
    """Wait for the environment server to be ready. Returns True on success."""
    print(f"Waiting for environment at {ENV_URL} ...", flush=True)
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(f"{ENV_URL}/", timeout=5)
            if resp.status_code == 200:
                print(f"  Environment ready (attempt {attempt}).", flush=True)
                return True
        except requests.ConnectionError:
            pass
        print(f"  Attempt {attempt}/{max_attempts} — retrying in {delay}s ...",
              flush=True)
        time.sleep(delay)
    return False


# ══════════════════════════════════════════════════════════
#  SYSTEM PROMPT
# ══════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are a data-cleaning agent. You receive a dirty dataset and must clean it.

You can take ONE of these actions (respond with EXACTLY one JSON object, nothing else):

1. Fix a cell value:
   {"action_type": "fix_cell", "row_index": <int>, "column_name": "<str>", "new_value": "<str>"}

2. Delete a duplicate row:
   {"action_type": "delete_row", "row_index": <int>}

3. Submit when done:
   {"action_type": "submit"}

RULES:
- Output ONLY the JSON object. No markdown, no explanation, no extra text.
- Fix ALL formatting issues before submitting (names, emails, phones, dates, cities).
- Delete exact duplicate rows (keep first occurrence).
- Fill missing (None) values using context and the provided rules.
- When all cells are clean, call submit.
"""


# ══════════════════════════════════════════════════════════
#  FORMAT OBSERVATION FOR THE LLM
# ══════════════════════════════════════════════════════════
def format_observation(obs: dict) -> str:
    """Convert the observation dict into a readable string for the LLM."""
    lines = [
        f"=== Task: {obs['task_id']} ===",
        f"Description: {obs['task_description']}",
        f"\n{obs['rules']}",
        (
            f"\nStep {obs['step_number']}/{obs['max_steps']} | "
            f"Score: {obs['current_score']:.2%} | "
            f"Active rows: {obs['num_active_rows']}/{obs['num_rows']}"
        ),
        f"Columns: {obs['columns']}",
        "\n--- Current Dataset ---",
    ]

    for row in obs["dataset"]:
        status = " [DELETED]" if row["deleted"] else ""
        lines.append(f"  Row {row['index']}{status}: {json.dumps(row['values'])}")

    if obs.get("action_history"):
        lines.append("\n--- Recent Actions ---")
        for act in obs["action_history"][-5:]:
            lines.append(f"  - {act}")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
#  PARSE LLM RESPONSE INTO AN ACTION
# ══════════════════════════════════════════════════════════
def parse_action(response_text: str) -> dict:
    """
    Extract a JSON action from the LLM's response.
    Falls back to submit on parse failure.
    """
    text = response_text.strip()

    # Strip markdown code fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text).strip()

    # Try 1: full text as JSON
    try:
        action = json.loads(text)
        if "action_type" in action:
            return action
    except json.JSONDecodeError:
        pass

    # Try 2: first JSON object containing "action_type"
    match = re.search(r'\{[^{}]*"action_type"[^{}]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try 3: any JSON object
    for m in re.findall(r'\{.*?\}', text, re.DOTALL):
        try:
            action = json.loads(m)
            if "action_type" in action:
                return action
        except json.JSONDecodeError:
            continue

    # Fallback
    print(f"  [WARN] Could not parse action — auto-submitting.", flush=True)
    return {"action_type": "submit"}


# ══════════════════════════════════════════════════════════
#  RUN ONE TASK
# ══════════════════════════════════════════════════════════
def run_task(client: OpenAI, task_id: str) -> float:
    """
    Run the agent on a single task.

    Emits [START], one [STEP] per action, and [END] to stdout.
    Returns the final score (0.0–1.0).
    """
    # ── Mandatory [START] ─────────────────────────────────
    log_start(task_id)

    # Reset environment
    result = env_reset(task_id)
    obs    = result["observation"]
    done   = result["done"]

    step_count = 0
    final_score = obs["current_score"]

    for step_num in range(1, MAX_AGENT_STEPS + 1):
        if done:
            break

        step_count = step_num

        # Build LLM prompt
        user_prompt = format_observation(obs)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ]

        # Call LLM via OpenAI client
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as exc:
            print(f"  [ERROR] LLM call failed: {exc}", flush=True)
            response_text = '{"action_type": "submit"}'

        # Parse action
        action = parse_action(response_text)

        # Send to environment
        result  = env_step(action)
        obs     = result["observation"]
        reward  = result["reward"]
        done    = result["done"]

        # ── Mandatory [STEP] ──────────────────────────────
        log_step(
            step=step_num,
            action=action,
            reward=reward["delta"],
            score=reward["score"],
            done=done,
            message=reward.get("message", ""),
        )

        final_score = reward["score"]

    # Grab properly graded final score if available
    if "final_grade" in result.get("info", {}):
        final_score = result["info"]["final_grade"]["score"]

    # ── Mandatory [END] ───────────────────────────────────
    log_end(task_id, final_score, step_count)

    return final_score


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════
def main() -> None:
    """Run the baseline agent on all 3 tasks."""
    print("=" * 60, flush=True)
    print("  Data Cleaning OpenEnv — Baseline Inference", flush=True)
    print(f"  Model    : {MODEL_NAME}", flush=True)
    print(f"  API Base : {API_BASE_URL}", flush=True)
    print(f"  Env URL  : {ENV_URL}", flush=True)
    print("=" * 60, flush=True)

    if not API_KEY:
        print("ERROR: HF_TOKEN (or OPENAI_API_KEY) is not set.", flush=True)
        sys.exit(1)

    # Wait for server
    if not wait_for_env():
        print("ERROR: Environment not reachable. Is the server running?",
              flush=True)
        print(f"  Tried: {ENV_URL}", flush=True)
        sys.exit(1)

    # Create OpenAI client (works with any OpenAI-compatible endpoint)
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # ── Run all tasks ────────────────────────────────────
    scores: dict[str, float] = {}
    for task_id in TASKS:
        score = run_task(client, task_id)
        scores[task_id] = score

    # ── Summary ──────────────────────────────────────────
    print("\n" + "=" * 60, flush=True)
    print("  RESULTS SUMMARY", flush=True)
    print("=" * 60, flush=True)

    for task_id, score in scores.items():
        difficulty = task_id.split("_")[0].upper()
        filled     = int(score * 30)
        bar        = "█" * filled + "░" * (30 - filled)
        print(f"  {difficulty:8s} | {bar} | {score:.2%}", flush=True)

    avg_score = sum(scores.values()) / len(scores)
    print(f"\n  Average Score : {avg_score:.2%}", flush=True)
    print("=" * 60, flush=True)
    print("Done!", flush=True)


if __name__ == "__main__":
    main()
