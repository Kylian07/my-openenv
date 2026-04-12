"""
test_agent.py — Simple example of how to use the Data Cleaning Environment

This script demonstrates:
1. How to connect to the environment
2. How to reset with a specific task
3. How to take actions (fix_cell, delete_row, submit)
4. How to interpret rewards and observations

Usage:
    python examples/test_agent.py
    
    Or with a live HF Space:
    python examples/test_agent.py --url https://kylian07-meta-env-rl.hf.space
"""

import requests
import argparse


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test the Data Cleaning Environment")
    parser.add_argument(
        "--url",
        default="http://localhost:7860",
        help="Environment URL (default: http://localhost:7860)"
    )
    parser.add_argument(
        "--task",
        default="easy_format_standardization",
        choices=[
            "easy_format_standardization",
            "medium_dedup_and_fill",
            "hard_full_pipeline"
        ],
        help="Task to run (default: easy_format_standardization)"
    )
    args = parser.parse_args()
    
    env_url = args.url
    task_id = args.task
    
    print("=" * 60)
    print("  Data Cleaning Environment — Test Agent")
    print("=" * 60)
    print(f"  URL:  {env_url}")
    print(f"  Task: {task_id}")
    print("=" * 60)
    
    # ── Step 1: Health Check ─────────────────────────────────
    print("\n[1] Health Check...")
    try:
        response = requests.get(f"{env_url}/", timeout=10)
        response.raise_for_status()
        print(f"    ✅ Server is running: {response.json()}")
    except Exception as e:
        print(f"    ❌ Server not reachable: {e}")
        print(f"    Make sure the server is running at {env_url}")
        return
    
    # ── Step 2: Reset Environment ────────────────────────────
    print(f"\n[2] Resetting environment with task: {task_id}...")
    response = requests.post(
        f"{env_url}/reset",
        json={"task_id": task_id},
        timeout=30
    )
    result = response.json()
    obs = result["observation"]
    
    print(f"    ✅ Environment reset!")
    print(f"    Initial score: {obs['current_score']:.2%}")
    print(f"    Rows: {obs['num_rows']}")
    print(f"    Columns: {obs['columns']}")
    print(f"    Max steps: {obs['max_steps']}")
    
    # Show first 2 rows of dirty data
    print("\n    Sample dirty data (first 2 rows):")
    for row in obs["dataset"][:2]:
        print(f"      Row {row['index']}: {row['values']}")
    
    # ── Step 3: Take a Fix Action ────────────────────────────
    print("\n[3] Taking action: fix_cell (row=0, col='name', val='John Doe')...")
    response = requests.post(
        f"{env_url}/step",
        json={
            "action": {
                "action_type": "fix_cell",
                "row_index": 0,
                "column_name": "name",
                "new_value": "John Doe"
            }
        },
        timeout=30
    )
    result = response.json()
    reward = result["reward"]
    
    print(f"    ✅ Action executed!")
    print(f"    New score: {reward['score']:.2%}")
    print(f"    Score change: {reward['delta']:+.4f}")
    print(f"    Message: {reward['message']}")
    
    # ── Step 4: Take Another Action ──────────────────────────
    print("\n[4] Taking action: fix_cell (row=0, col='email', val='john@gmail.com')...")
    response = requests.post(
        f"{env_url}/step",
        json={
            "action": {
                "action_type": "fix_cell",
                "row_index": 0,
                "column_name": "email",
                "new_value": "john@gmail.com"
            }
        },
        timeout=30
    )
    result = response.json()
    reward = result["reward"]
    
    print(f"    ✅ Action executed!")
    print(f"    New score: {reward['score']:.2%}")
    print(f"    Score change: {reward['delta']:+.4f}")
    
    # ── Step 5: Check State ──────────────────────────────────
    print("\n[5] Checking current state...")
    response = requests.get(f"{env_url}/state", timeout=10)
    state = response.json()
    
    print(f"    Task: {state['task_id']}")
    print(f"    Step: {state['step_number']}/{state['max_steps']}")
    print(f"    Score: {state['score']:.2%}")
    print(f"    Done: {state['done']}")
    
    # ── Step 6: Submit (End Episode) ─────────────────────────
    print("\n[6] Submitting dataset for final grading...")
    response = requests.post(
        f"{env_url}/step",
        json={
            "action": {
                "action_type": "submit"
            }
        },
        timeout=30
    )
    result = response.json()
    
    print(f"    ✅ Submitted!")
    print(f"    Final score: {result['reward']['score']:.2%}")
    print(f"    Done: {result['done']}")
    
    if "final_grade" in result.get("info", {}):
        grade = result["info"]["final_grade"]
        print(f"\n    Final Grade Details:")
        print(f"      Total checks: {grade['breakdown']['total_checks']}")
        print(f"      Correct: {grade['breakdown']['correct_checks']}")
        print(f"      Remaining issues: {len(grade['details'])}")
        
        if grade["details"]:
            print(f"\n    First 3 issues:")
            for issue in grade["details"][:3]:
                print(f"      - {issue}")
    
    # ── Summary ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Test Complete!")
    print("=" * 60)
    print("""
    This example showed:
    ✅ Connecting to the environment
    ✅ Resetting with a task
    ✅ Taking fix_cell actions
    ✅ Checking state
    ✅ Submitting for final grade
    
    Next steps:
    - Build a smarter agent that fixes ALL cells
    - Try the medium and hard tasks
    - Integrate with an LLM (see inference.py)
    """)


if __name__ == "__main__":
    main()