"""
Baseline inference script for the Data Cleaning OpenEnv.

Uses the OpenAI API client to run an LLM agent against the environment.
The agent looks at the dirty data, decides what to fix, and submits.

Usage:
    SET API_BASE_URL=https://router.huggingface.co/hf-inference/v1
    SET MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
    SET HF_TOKEN=hf_xxxxx
    SET ENV_URL=http://localhost:7860
    python inference.py
"""

import os
import json
import re
import requests
import time
from openai import OpenAI


# ══════════════════════════════════════════════════════════
#  CONFIGURATION — reads from environment variables
# ══════════════════════════════════════════════════════════
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
API_KEY = os.environ.get("HF_TOKEN", os.environ.get("OPENAI_API_KEY", ""))
ENV_URL = os.environ.get("ENV_URL", "http://localhost:7860")

MAX_AGENT_STEPS = 50     # Max actions per task
TEMPERATURE = 0.0        # Deterministic output
MAX_TOKENS = 2048        # Max response length

# The 3 tasks to run
TASKS = [
    "easy_format_standardization",
    "medium_dedup_and_fill",
    "hard_full_pipeline",
]

# ══════════════════════════════════════════════════════════
#  SYSTEM PROMPT — Instructions for the LLM agent
# ══════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are a data-cleaning agent. You receive a dirty dataset and must clean it.

You can take these actions (respond with EXACTLY one JSON object per turn):

1. Fix a cell value:
   {"action_type": "fix_cell", "row_index": <int>, "column_name": "<str>", "new_value": "<str>"}

2. Delete a duplicate row:
   {"action_type": "delete_row", "row_index": <int>}

3. Submit the cleaned dataset:
   {"action_type": "submit"}

IMPORTANT RULES:
- Respond with ONLY the JSON object. No explanations, no markdown, no extra text.
- Fix ALL dirty cells before submitting.
- Delete duplicate rows (keep the first occurrence).
- Fill missing (null/None) values using context and the rules provided.
- Follow the formatting rules EXACTLY.
- Work systematically: go row by row, column by column.
- When everything is clean, submit.

Example response (just the JSON, nothing else):
{"action_type": "fix_cell", "row_index": 0, "column_name": "name", "new_value": "John Doe"}
"""


# ══════════════════════════════════════════════════════════
#  ENVIRONMENT API HELPERS
# ══════════════════════════════════════════════════════════
def env_reset(task_id: str) -> dict:
    """Call the environment's reset endpoint."""
    resp = requests.post(
        f"{ENV_URL}/reset",
        json={"task_id": task_id},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def env_step(action: dict) -> dict:
    """Call the environment's step endpoint."""
    resp = requests.post(
        f"{ENV_URL}/step",
        json={"action": action},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()


# ══════════════════════════════════════════════════════════
#  FORMAT OBSERVATION FOR THE LLM
# ══════════════════════════════════════════════════════════
def format_observation(obs: dict) -> str:
    """
    Convert the observation dict into a readable string
    that the LLM can understand.
    """
    lines = []
    lines.append(f"=== Task: {obs['task_id']} ===")
    lines.append(f"Description: {obs['task_description']}")
    lines.append(f"\n{obs['rules']}")
    lines.append(
        f"\nStep {obs['step_number']}/{obs['max_steps']} | "
        f"Current Score: {obs['current_score']:.2%}"
    )
    lines.append(
        f"Active rows: {obs['num_active_rows']}/{obs['num_rows']}"
    )
    lines.append(f"\nColumns: {obs['columns']}")

    # Show the dataset
    lines.append("\n--- Current Dataset ---")
    for row in obs["dataset"]:
        status = " [DELETED]" if row["deleted"] else ""
        values_str = json.dumps(row["values"], ensure_ascii=False)
        lines.append(f"  Row {row['index']}{status}: {values_str}")

    # Show recent actions
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
    Handles various formatting issues (markdown blocks, extra text).
    """
    text = response_text.strip()

    # Remove markdown code blocks if present
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    # Try 1: Parse the entire text as JSON
    try:
        action = json.loads(text)
        if "action_type" in action:
            return action
    except json.JSONDecodeError:
        pass

    # Try 2: Find a JSON object containing "action_type"
    match = re.search(r'\{[^{}]*"action_type"[^{}]*\}', text)
    if match:
        try:
            action = json.loads(match.group())
            return action
        except json.JSONDecodeError:
            pass

    # Try 3: More aggressive search for any JSON object
    matches = re.findall(r'\{.*?\}', text, re.DOTALL)
    for m in matches:
        try:
            action = json.loads(m)
            if "action_type" in action:
                return action
        except json.JSONDecodeError:
            continue

    # Fallback: submit (better than crashing)
    print(f"  [WARN] Could not parse action from response. Auto-submitting.")
    print(f"         Response was: {text[:200]}")
    return {"action_type": "submit"}


# ══════════════════════════════════════════════════════════
#  RUN ONE TASK
# ══════════════════════════════════════════════════════════
def run_task(client: OpenAI, task_id: str) -> float:
    """
    Run the agent on a single task.
    
    Returns: final score (0.0 to 1.0)
    """
    print(f"\n{'=' * 60}")
    print(f"  TASK: {task_id}")
    print(f"{'=' * 60}")

    # Reset environment for this task
    result = env_reset(task_id)
    obs = result["observation"]
    done = result["done"]

    print(f"  Initial score: {obs['current_score']:.2%}")
    print(f"  Rows: {obs['num_rows']}, Max steps: {obs['max_steps']}")

    for step_num in range(1, MAX_AGENT_STEPS + 1):
        if done:
            break

        # Format observation for the LLM
        user_prompt = format_observation(obs)

        # Build messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        # Call the LLM
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as e:
            print(f"  [ERROR] LLM call failed: {e}")
            # On error, submit what we have
            response_text = '{"action_type": "submit"}'

        # Parse LLM response into action
        action = parse_action(response_text)

        # Log the action
        action_type = action.get("action_type", "?")
        row = action.get("row_index", "")
        col = action.get("column_name", "")
        val = action.get("new_value", "")
        if val and len(str(val)) > 30:
            val = str(val)[:30] + "..."
        print(f"  Step {step_num:2d}: {action_type:10s} "
              f"row={row} col={col} val={val}")

        # Send action to environment
        result = env_step(action)
        obs = result["observation"]
        reward = result["reward"]
        done = result["done"]

        print(f"           Score: {reward['score']:.2%} "
              f"(delta: {reward['delta']:+.4f}) "
              f"| {reward['message'][:50]}")

    # ── Get final score ───────────────────────────────────
    final_score = obs["current_score"]

    if "final_grade" in result.get("info", {}):
        final_grade = result["info"]["final_grade"]
        final_score = final_grade["score"]
        print(f"\n  FINAL SCORE: {final_score:.2%}")
        breakdown = final_grade.get("breakdown", {})
        print(f"  Total checks: {breakdown.get('total_checks', '?')}")
        print(f"  Correct: {breakdown.get('correct_checks', '?')}")

        # Show first few remaining issues
        details = final_grade.get("details", [])
        if details:
            print(f"  Remaining issues ({len(details)}):")
            for d in details[:5]:
                print(f"    - {d}")
            if len(details) > 5:
                print(f"    ... and {len(details) - 5} more")
        else:
            print("  No remaining issues! Perfect score!")

    return final_score


# ══════════════════════════════════════════════════════════
#  MAIN — Run all tasks
# ══════════════════════════════════════════════════════════
def main():
    """Run the baseline agent on all 3 tasks."""
    print("=" * 60)
    print("  Data Cleaning OpenEnv — Baseline Inference")
    print(f"  Model:    {MODEL_NAME}")
    print(f"  API Base: {API_BASE_URL}")
    print(f"  Env URL:  {ENV_URL}")
    print("=" * 60)

    # Create OpenAI client
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # Wait for environment to be ready
    print("\nWaiting for environment to be ready...")
    for attempt in range(15):
        try:
            resp = requests.get(f"{ENV_URL}/", timeout=5)
            if resp.status_code == 200:
                print("Environment is ready!\n")
                break
        except requests.ConnectionError:
            pass
        print(f"  Attempt {attempt + 1}/15 — retrying in 3s...")
        time.sleep(3)
    else:
        print("ERROR: Environment not reachable. Is the server running?")
        print(f"  Tried: {ENV_URL}")
        return

    # Run all tasks
    scores = {}
    for task_id in TASKS:
        score = run_task(client, task_id)
        scores[task_id] = score

    # ── Print Summary ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)

    for task_id, score in scores.items():
        # Extract difficulty from task_id
        difficulty = task_id.split("_")[0].upper()
        # Create visual bar
        filled = int(score * 30)
        bar = "█" * filled + "░" * (30 - filled)
        print(f"  {difficulty:8s} | {bar} | {score:.2%}")

    avg_score = sum(scores.values()) / len(scores)
    print(f"\n  Average Score: {avg_score:.2%}")
    print("=" * 60)
    print("\nDone!")


if __name__ == "__main__":
    main()