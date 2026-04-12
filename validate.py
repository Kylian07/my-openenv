"""
Pre-Submission Validator for the Data Cleaning OpenEnv.

Runs all checklist gates and prints PASS / FAIL for each.
Run this before submitting your HF Space.

Usage:
    # Start the environment server first (in another terminal):
    #   cd src && uvicorn main:app --host 0.0.0.0 --port 7860
    #
    # Then run this validator:
    #   python validate.py
    #
    # Or test against the live HF Space:
    #   set ENV_URL=https://kylian07-meta-env-rl.hf.space
    #   python validate.py
"""

import os
import sys
import json
import yaml       # pip install pyyaml
import requests

# ── Force UTF-8 output on Windows (fixes → / emoji printing) ──
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ENV_URL = os.environ.get("ENV_URL", "http://localhost:7860")

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results: list[tuple[str, str, str]] = []   # (check_name, status, detail)


def _safe(text: str) -> str:
    """Replace characters that the console codec can't handle."""
    return text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")


def check(name: str, passed: bool, detail: str = "") -> None:
    status = PASS if passed else FAIL
    results.append((name, status, detail))
    icon = "[PASS]" if passed else "[FAIL]"
    try:
        print(f"  {icon}  {name}", flush=True)
        if detail:
            print(f"         {detail}", flush=True)
    except UnicodeEncodeError:
        print(f"  {icon}  {_safe(name)}", flush=True)
        if detail:
            print(f"         {_safe(detail)}", flush=True)


def warn(name: str, detail: str = "") -> None:
    results.append((name, WARN, detail))
    print(f"  [WARN]  {name}", flush=True)
    if detail:
        print(f"         {detail}", flush=True)


# ══════════════════════════════════════════════════════════
#  GATE 1 — Environment Variables
# ══════════════════════════════════════════════════════════
def gate_env_vars() -> None:
    print("\n[1] Checking required environment variables ...")
    for var in ("API_BASE_URL", "MODEL_NAME", "HF_TOKEN"):
        val = os.environ.get(var, "")
        if val:
            check(f"{var} is set", True, f"= {val[:30]}{'...' if len(val) > 30 else ''}")
        else:
            check(f"{var} is set", False, "NOT set — add to your environment before submitting")


# ══════════════════════════════════════════════════════════
#  GATE 2 — inference.py exists in root
# ══════════════════════════════════════════════════════════
def gate_inference_file() -> None:
    print("\n[2] Checking inference.py in root directory ...")
    exists = os.path.isfile("inference.py")
    check("inference.py exists in root", exists,
          "Found." if exists else "NOT found — must be in the repository root.")

    if exists:
        with open("inference.py", "r", encoding="utf-8") as f:
            content = f.read()
        has_start = "[START]" in content
        has_step  = "[STEP]"  in content
        has_end   = "[END]"   in content
        check("inference.py emits [START] logs", has_start)
        check("inference.py emits [STEP] logs",  has_step)
        check("inference.py emits [END] logs",   has_end)

        has_openai_client = "OpenAI(" in content
        check("inference.py uses OpenAI client", has_openai_client)

        for var in ("API_BASE_URL", "MODEL_NAME", "HF_TOKEN"):
            check(f'inference.py reads {var}', var in content)


# ══════════════════════════════════════════════════════════
#  GATE 3 — openenv.yaml compliance
# ══════════════════════════════════════════════════════════
def gate_openenv_yaml() -> None:
    print("\n[3] Validating openenv.yaml ...")

    yaml_path = "openenv.yaml"
    if not os.path.isfile(yaml_path):
        check("openenv.yaml exists", False, "File not found")
        return
    check("openenv.yaml exists", True)

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            spec = yaml.safe_load(f)
    except Exception as exc:
        check("openenv.yaml parses as valid YAML", False, str(exc))
        return
    check("openenv.yaml parses as valid YAML", True)

    # Required top-level fields
    for field in ("name", "description", "version", "interface",
                  "endpoints", "tasks", "action_space",
                  "observation_space", "reward"):
        check(f"openenv.yaml has field: {field}", field in spec)

    # Typed model refs
    iface = spec.get("interface", {})
    for model_key in ("observation_model", "action_model", "reward_model"):
        check(f"interface.{model_key} defined", model_key in iface,
              iface.get(model_key, "MISSING"))

    # Endpoints
    endpoints = spec.get("endpoints", {})
    for ep in ("reset", "step", "state"):
        check(f"endpoint '{ep}' defined", ep in endpoints,
              endpoints.get(ep, "MISSING"))

    # At least 3 tasks
    tasks = spec.get("tasks", [])
    check(f"At least 3 tasks defined (found {len(tasks)})", len(tasks) >= 3)

    # Reward range
    reward = spec.get("reward", {})
    rrange = reward.get("range", [])
    check("reward range is [0.0, 1.0]",
          len(rrange) == 2 and rrange[0] == 0.0 and rrange[1] == 1.0,
          str(rrange))


# ══════════════════════════════════════════════════════════
#  GATE 4 — HF Space / local server reachability
# ══════════════════════════════════════════════════════════
def gate_server_health() -> None:
    print(f"\n[4] Pinging environment at {ENV_URL} ...")

    try:
        resp = requests.get(f"{ENV_URL}/", timeout=10)
        ok   = resp.status_code == 200
        check(f"GET / returns 200", ok, f"status={resp.status_code}")
        if ok:
            data = resp.json()
            check("Response has 'status' field",
                  "status" in data, data.get("status", "MISSING"))
    except Exception as exc:
        check("GET / reachable", False, str(exc))
        return   # No point in further server checks


# ══════════════════════════════════════════════════════════
#  GATE 5 — /reset() responds correctly per task
# ══════════════════════════════════════════════════════════
def gate_reset_endpoint() -> None:
    print(f"\n[5] Testing /reset for all tasks ...")

    task_ids = [
        "easy_format_standardization",
        "medium_dedup_and_fill",
        "hard_full_pipeline",
    ]

    for task_id in task_ids:
        try:
            resp = requests.post(
                f"{ENV_URL}/reset",
                json={"task_id": task_id},
                timeout=15,
            )
            ok = resp.status_code == 200
            if ok:
                data = resp.json()
                has_obs    = "observation" in data
                has_reward = "reward"      in data
                has_done   = "done"        in data
                score      = data.get("reward", {}).get("score", -1)
                valid_score = 0.0 <= score <= 1.0

                check(f"/reset returns 200 for '{task_id}'", True)
                check(f"  → has observation",  has_obs)
                check(f"  → has reward",       has_reward)
                check(f"  → has done flag",    has_done)
                check(f"  → score in [0,1]: {score:.4f}", valid_score)
            else:
                check(f"/reset '{task_id}'", False,
                      f"HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as exc:
            check(f"/reset '{task_id}'", False, str(exc))


# ══════════════════════════════════════════════════════════
#  GATE 6 — /step() works
# ══════════════════════════════════════════════════════════
def gate_step_endpoint() -> None:
    print(f"\n[6] Testing /step endpoint ...")

    # First reset
    try:
        requests.post(
            f"{ENV_URL}/reset",
            json={"task_id": "easy_format_standardization"},
            timeout=10,
        )
    except Exception:
        check("/step (setup reset)", False, "Could not reset for step test")
        return

    # Now take a fix_cell action
    action = {
        "action_type": "fix_cell",
        "row_index": 0,
        "column_name": "name",
        "new_value": "John Doe",
    }
    try:
        resp = requests.post(
            f"{ENV_URL}/step",
            json={"action": action},
            timeout=15,
        )
        ok = resp.status_code == 200
        check("/step returns 200", ok, f"status={resp.status_code}")
        if ok:
            data  = resp.json()
            score = data.get("reward", {}).get("score", -1)
            delta = data.get("reward", {}).get("delta", None)
            check("  → reward.score in [0,1]", 0.0 <= score <= 1.0,
                  str(score))
            check("  → reward.delta present", delta is not None, str(delta))
    except Exception as exc:
        check("/step reachable", False, str(exc))


# ══════════════════════════════════════════════════════════
#  GATE 7 — /state() works
# ══════════════════════════════════════════════════════════
def gate_state_endpoint() -> None:
    print(f"\n[7] Testing /state endpoint ...")

    try:
        resp = requests.get(f"{ENV_URL}/state", timeout=10)
        ok   = resp.status_code == 200
        check("/state returns 200", ok, f"status={resp.status_code}")
        if ok:
            data = resp.json()
            for field in ("task_id", "step_number", "max_steps",
                          "done", "score", "num_active_rows"):
                check(f"  → state has '{field}'", field in data)
    except Exception as exc:
        check("/state reachable", False, str(exc))


# ══════════════════════════════════════════════════════════
#  GATE 8 — Graders produce valid scores for all 3 tasks
# ══════════════════════════════════════════════════════════
def gate_graders() -> None:
    print("\n[8] Running graders for all 3 tasks ...")

    # Try to import the grader directly from src/
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
        from graders import grade  # type: ignore
        from tasks import TASKS    # type: ignore
    except ImportError as exc:
        check("Import graders from src/", False, str(exc))
        return
    check("Import graders from src/", True)

    for task_id, task_def in TASKS.items():
        # Grade the dirty data (expect low score)
        dirty_result = grade(task_def, task_def["dirty_data"], set())
        dirty_score  = dirty_result["score"]

        # The environment stores ALL rows in _dataset (including deleted ones),
        # it never removes them — it just marks them deleted.
        # So to simulate a perfectly cleaned state, we reconstruct the full
        # dataset at its original length, mapping clean_data rows into the
        # non-deleted positions.
        import copy
        deleted_set = set(task_def["rows_to_delete"])
        full_clean  = copy.deepcopy(task_def["dirty_data"])
        clean_idx   = 0
        for i in range(len(full_clean)):
            if i in deleted_set:
                continue
            full_clean[i] = task_def["clean_data"][clean_idx]
            clean_idx += 1

        clean_result = grade(task_def, full_clean, deleted_set)
        clean_score  = clean_result["score"]

        valid_dirty = 0.0 <= dirty_score <= 1.0
        valid_clean = 0.0 <= clean_score <= 1.0
        perfect     = clean_score == 1.0

        check(f"Task '{task_id}' — dirty score in [0,1]: {dirty_score:.4f}",
              valid_dirty)
        check(f"Task '{task_id}' — clean score = 1.0:    {clean_score:.4f}",
              perfect and valid_clean,
              "" if perfect else f"Expected 1.0, got {clean_score}")


# ══════════════════════════════════════════════════════════
#  FINAL REPORT
# ══════════════════════════════════════════════════════════
def final_report() -> None:
    total  = len(results)
    passed = sum(1 for _, s, _ in results if s == PASS)
    warned = sum(1 for _, s, _ in results if s == WARN)
    failed = sum(1 for _, s, _ in results if s == FAIL)

    print("\n" + "=" * 60)
    print("  PRE-SUBMISSION VALIDATION REPORT")
    print("=" * 60)
    print(f"  Total checks : {total}")
    print(f"  Passed       : {passed}")
    print(f"  Warnings     : {warned}")
    print(f"  Failed       : {failed}")
    print("=" * 60)

    if failed == 0:
        print("\n  *** ALL CHECKS PASSED — You are ready to submit! ***\n")
    else:
        print(f"\n  !!! {failed} check(s) FAILED — fix them before submitting. !!!\n")
        print("  Failed checks:")
        for name, status, detail in results:
            if status == FAIL:
                print(f"    [FAIL] {name}")
                if detail:
                    print(f"           {detail}")
        print()


# ══════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  Data Cleaning OpenEnv — Pre-Submission Validator")
    print(f"  Environment URL: {ENV_URL}")
    print("=" * 60)

    gate_env_vars()
    gate_inference_file()
    gate_openenv_yaml()
    gate_server_health()
    gate_reset_endpoint()
    gate_step_endpoint()
    gate_state_endpoint()
    gate_graders()

    final_report()

    # Exit with non-zero if any check failed (useful in CI)
    failed_count = sum(1 for _, s, _ in results if s == FAIL)
    sys.exit(1 if failed_count > 0 else 0)
