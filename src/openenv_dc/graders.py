"""
Deterministic graders that score agent performance 0.0 → 1.0

Scoring works by comparing each cell in the agent's dataset
against the ground truth (clean_data), cell by cell.
"""

from typing import List, Dict, Set


def grade(task_def: dict,
          current_data: List[dict],
          deleted_indices: Set[int]) -> dict:
    """
    Score the current dataset state against ground truth.

    How scoring works:
      1. Check if correct rows were deleted (duplicates)
      2. Check each cell in non-deleted rows against ground truth
      3. score = correct_checks / total_checks

    Returns:
      {
        "score": 0.0 to 1.0,
        "breakdown": {...},
        "details": ["list of remaining issues"]
      }
    """
    clean_data = task_def["clean_data"]
    expected_deletes = set(task_def["rows_to_delete"])
    columns = task_def["columns"]

    total_checks = 0
    correct_checks = 0
    details = []

    # ── PART 1: Check deletions ───────────────────────────
    # Did the agent delete the right rows?
    delete_checks = len(expected_deletes) if expected_deletes else 0
    delete_correct = 0

    if expected_deletes:
        for idx in expected_deletes:
            total_checks += 1
            if idx in deleted_indices:
                delete_correct += 1
                correct_checks += 1
            else:
                details.append(
                    f"Row {idx} should be deleted (duplicate) but wasn't"
                )

        # Penalize WRONG deletions (agent deleted a good row)
        false_deletes = deleted_indices - expected_deletes
        for idx in false_deletes:
            total_checks += 1  # counts as a wrong answer
            details.append(f"Row {idx} was incorrectly deleted")

    # ── PART 2: Check cell values ─────────────────────────
    # Compare each cell against the correct answer
    clean_idx = 0
    for orig_idx, row in enumerate(current_data):

        # Skip rows that SHOULD be deleted
        if orig_idx in expected_deletes:
            continue

        # If agent deleted a row that shouldn't be deleted
        if orig_idx in deleted_indices:
            for col in columns:
                total_checks += 1
                details.append(
                    f"Row {orig_idx}, col '{col}': "
                    f"row was incorrectly deleted"
                )
            clean_idx += 1
            continue

        # Make sure we don't go out of bounds
        if clean_idx >= len(clean_data):
            break

        expected_row = clean_data[clean_idx]

        # Check each cell
        for col in columns:
            total_checks += 1

            # Get current value (what agent produced)
            current_val = str(row.get(col, "")).strip() \
                if row.get(col) is not None else ""

            # Get expected value (correct answer)
            expected_val = str(expected_row.get(col, "")).strip() \
                if expected_row.get(col) is not None else ""

            if current_val == expected_val:
                correct_checks += 1
            else:
                details.append(
                    f"Row {orig_idx}, col '{col}': "
                    f"got '{current_val}', expected '{expected_val}'"
                )

        clean_idx += 1

    # ── Calculate final score ─────────────────────────────
    # Standard formula: correct / total
    raw_score = correct_checks / max(total_checks, 1)

    # Hackathon Rule: Scores must be STRICTLY between 0 and 1 (non-inclusive).
    # We map [0, 1] to [0.1, 0.9] to be extremely safe.
    clamped_score = 0.1 + (raw_score * 0.8)

    breakdown = {
        "check_total": total_checks,
        "check_correct": correct_checks,
        "deletion_accuracy_clamped": 0.1 + (0.8 * (
            delete_correct / max(delete_checks, 1)
            if delete_checks else 1.0
        )),
        "cell_accuracy_clamped": 0.1 + (0.8 * raw_score),
    }

    return {
        "score": round(clamped_score, 4),
        "breakdown": breakdown,
        "details": details,
    }