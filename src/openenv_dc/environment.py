"""
Core Data Cleaning Environment — implements reset / step / state.

This is where all the logic lives:
  - reset(): Start fresh with dirty data
  - step():  Process an agent action and return results
  - state(): Return current status
"""

import copy
from typing import Optional, List, Set

from .models import (
    Action, ActionType, DataRow, Observation, Reward,
    StepResult, StateResponse
)
from .tasks import get_task, FORMATTING_RULES
from .graders import grade


class DataCleaningEnv:
    """
    OpenEnv-compliant data-cleaning environment.
    
    The agent receives a dirty dataset and must clean it by:
      - Fixing cell values (formatting, missing, outliers)
      - Deleting duplicate rows
      - Submitting when done
    """

    def __init__(self):
        """Initialize with empty state."""
        self._task_def: Optional[dict] = None
        self._dataset: List[dict] = []          # Current cell values
        self._deleted: Set[int] = set()          # Indices of deleted rows
        self._step_num: int = 0
        self._max_steps: int = 0
        self._done: bool = True
        self._history: List[str] = []            # Action log
        self._prev_score: float = 0.5            # Start in-between to satisfy (0,1) range

    # ══════════════════════════════════════════════════════════
    #  reset() — Start a new episode
    # ══════════════════════════════════════════════════════════
    def reset(self, task_id: str) -> StepResult:
        """
        Reset the environment with a specific task.
        
        Args:
            task_id: One of "easy_format_standardization",
                     "medium_dedup_and_fill", "hard_full_pipeline"
        
        Returns:
            StepResult with initial observation
        """
        # Load task definition
        self._task_def = get_task(task_id)

        # Create a fresh copy of the dirty data
        self._dataset = copy.deepcopy(self._task_def["dirty_data"])

        # Reset all state
        self._deleted = set()
        self._step_num = 0
        self._max_steps = self._task_def["max_steps"]
        self._done = False
        self._history = []

        # Calculate initial score (before any cleaning)
        self._prev_score = self._compute_score()

        # Build observation and reward
        obs = self._make_observation()
        reward = Reward(
            score=self._prev_score,
            delta=0.0001,  # Near-zero but strictly > 0
            message="Environment reset. Begin cleaning the dataset."
        )

        return StepResult(
            observation=obs,
            reward=reward,
            done=False,
            info={"task_difficulty": self._task_def["difficulty"]}
        )

    # ══════════════════════════════════════════════════════════
    #  step() — Process one agent action
    # ══════════════════════════════════════════════════════════
    def step(self, action: Action) -> StepResult:
        """
        Process one action from the agent.
        
        Args:
            action: The action to take (fix_cell, delete_row, or submit)
        
        Returns:
            StepResult with new observation, reward, done flag, and info
        """
        # ── Guard: episode already finished ───────────────
        if self._done:
            obs = self._make_observation()
            return StepResult(
                observation=obs,
                reward=Reward(
                    score=self._prev_score,
                    delta=0.0001,
                    message="Episode already done. Call reset() to start a new one."
                ),
                done=True,
                info={"error": "Episode is already done. Call reset()."}
            )

        # ── Increment step counter ────────────────────────
        self._step_num += 1
        msg = ""
        error = None

        # ── Execute the action ────────────────────────────
        if action.action_type == ActionType.FIX_CELL:
            error = self._do_fix_cell(action)
            if error:
                msg = f"Invalid fix_cell: {error}"
            else:
                msg = (
                    f"Fixed row {action.row_index}, "
                    f"col '{action.column_name}' -> '{action.new_value}'"
                )

        elif action.action_type == ActionType.DELETE_ROW:
            error = self._do_delete_row(action)
            if error:
                msg = f"Invalid delete_row: {error}"
            else:
                msg = f"Deleted row {action.row_index}"

        elif action.action_type == ActionType.SUBMIT:
            self._done = True
            msg = "Dataset submitted for final grading."

        # ── Record action in history ──────────────────────
        self._history.append(msg)

        # ── Compute reward ────────────────────────────────
        new_score = self._compute_score()
        delta = new_score - self._prev_score

        # Small penalty for invalid actions (discourages random actions)
        if error:
            delta -= 0.01

        self._prev_score = new_score

        # ── Check if max steps reached ────────────────────
        if self._step_num >= self._max_steps and not self._done:
            self._done = True
            msg += " (Max steps reached - auto-submitting.)"

        # ── Build response ────────────────────────────────
        obs = self._make_observation()
        reward = Reward(
            score=new_score,
            delta=round(delta, 4),
            message=msg
        )

        info = {}
        if error:
            info["error"] = error

        # Include final grade when episode ends
        if self._done:
            grade_result = grade(
                self._task_def,
                self._dataset,
                self._deleted,
            )
            info["final_grade"] = grade_result

        return StepResult(
            observation=obs,
            reward=reward,
            done=self._done,
            info=info
        )

    # ══════════════════════════════════════════════════════════
    #  state() — Get current state summary
    # ══════════════════════════════════════════════════════════
    def state(self) -> StateResponse:
        """Return a summary of the current environment state."""
        return StateResponse(
            task_id=self._task_def["task_id"] if self._task_def else "",
            step_number=self._step_num,
            max_steps=self._max_steps,
            done=self._done,
            score=self._prev_score,
            num_active_rows=len(self._dataset) - len(self._deleted),
            action_count=len(self._history),
        )

    # ══════════════════════════════════════════════════════════
    #  INTERNAL HELPERS (private methods)
    # ══════════════════════════════════════════════════════════

    def _do_fix_cell(self, action: Action) -> Optional[str]:
        """
        Execute a fix_cell action. Returns error message or None.
        """
        # Validate all required fields are present
        if action.row_index is None:
            return "row_index is required"
        if action.column_name is None:
            return "column_name is required"
        if action.new_value is None:
            return "new_value is required"

        # Validate row_index is in range
        if action.row_index < 0 or action.row_index >= len(self._dataset):
            return (
                f"row_index {action.row_index} out of range "
                f"(0 to {len(self._dataset) - 1})"
            )

        # Can't fix a deleted row
        if action.row_index in self._deleted:
            return f"row {action.row_index} is already deleted"

        # Validate column exists
        if action.column_name not in self._task_def["columns"]:
            return (
                f"unknown column '{action.column_name}'. "
                f"Valid columns: {self._task_def['columns']}"
            )

        # ── Apply the fix ─────────────────────────────────
        self._dataset[action.row_index][action.column_name] = action.new_value
        return None  # No error

    def _do_delete_row(self, action: Action) -> Optional[str]:
        """
        Execute a delete_row action. Returns error message or None.
        """
        if action.row_index is None:
            return "row_index is required"

        if action.row_index < 0 or action.row_index >= len(self._dataset):
            return (
                f"row_index {action.row_index} out of range "
                f"(0 to {len(self._dataset) - 1})"
            )

        if action.row_index in self._deleted:
            return f"row {action.row_index} is already deleted"

        # ── Mark as deleted ───────────────────────────────
        self._deleted.add(action.row_index)
        return None  # No error

    def _compute_score(self) -> float:
        """Calculate current score by grading against ground truth."""
        if not self._task_def:
            return 0.5  # Neutral score if no task loaded
        result = grade(self._task_def, self._dataset, self._deleted)
        return result["score"]

    def _make_observation(self) -> Observation:
        """Build the observation object that the agent sees."""
        rows = []
        for i, row_data in enumerate(self._dataset):
            rows.append(DataRow(
                index=i,
                values=row_data,
                deleted=(i in self._deleted),
            ))

        return Observation(
            task_id=self._task_def["task_id"],
            task_description=self._task_def["description"],
            rules=FORMATTING_RULES,
            dataset=rows,
            columns=self._task_def["columns"],
            column_descriptions=self._task_def["column_descriptions"],
            num_rows=len(self._dataset),
            num_active_rows=len(self._dataset) - len(self._deleted),
            step_number=self._step_num,
            max_steps=self._max_steps,
            action_history=self._history[-10:],  # Only last 10 actions
            current_score=self._prev_score,
        )