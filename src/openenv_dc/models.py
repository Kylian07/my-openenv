"""Typed Pydantic models for the Data Cleaning OpenEnv environment."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


# ────────────────────────────────────────────────────────────
# ACTION SPACE — What the agent CAN DO
# ────────────────────────────────────────────────────────────
class ActionType(str, Enum):
    """Three possible actions the agent can take."""
    FIX_CELL = "fix_cell"        # Change a cell's value
    DELETE_ROW = "delete_row"    # Remove a duplicate/invalid row
    SUBMIT = "submit"            # Submit cleaned dataset for grading


class Action(BaseModel):
    """
    One action the agent takes per step.
    
    Examples:
      {"action_type": "fix_cell", "row_index": 0, "column_name": "name", "new_value": "John Doe"}
      {"action_type": "delete_row", "row_index": 5}
      {"action_type": "submit"}
    """
    action_type: ActionType = Field(..., description="Type of action to perform")
    row_index: Optional[int] = Field(None, description="0-based row index to act on")
    column_name: Optional[str] = Field(None, description="Column name to act on")
    new_value: Optional[str] = Field(None, description="Replacement value (for fix_cell)")


# ────────────────────────────────────────────────────────────
# OBSERVATION SPACE — What the agent SEES
# ────────────────────────────────────────────────────────────
class DataRow(BaseModel):
    """Represents one row in the dataset."""
    index: int                              # Row number (0-based)
    values: Dict[str, Optional[str]]        # Column name → cell value
    deleted: bool = False                   # Whether this row was deleted


class Observation(BaseModel):
    """
    Everything the agent sees after each step.
    This is like the agent's 'eyes' into the environment.
    """
    task_id: str                                    # Which task is running
    task_description: str                           # Human-readable instructions
    rules: str                                      # Formatting rules to follow
    dataset: List[DataRow]                          # All rows (current state)
    columns: List[str]                              # Column names
    column_descriptions: Dict[str, str]             # What each column expects
    num_rows: int                                   # Total rows (including deleted)
    num_active_rows: int                            # Rows not deleted
    step_number: int                                # Current step
    max_steps: int                                  # Maximum allowed steps
    action_history: List[str]                       # Last few actions taken
    current_score: float                            # Real-time score (0.0-1.0)


# ────────────────────────────────────────────────────────────
# REWARD — Feedback signal to the agent
# ────────────────────────────────────────────────────────────
class Reward(BaseModel):
    """Reward signal returned after each step."""
    score: float = Field(..., ge=0.0, le=1.0, description="Current overall score")
    delta: float = Field(0.0, description="Change in score from last step")
    message: str = ""                               # Human-readable feedback


# ────────────────────────────────────────────────────────────
# API REQUEST/RESPONSE SCHEMAS
# ────────────────────────────────────────────────────────────
class StepResult(BaseModel):
    """What step() and reset() return."""
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any] = {}


class ResetRequest(BaseModel):
    """Request body for reset endpoint."""
    task_id: str = "easy_format_standardization"


class StepRequest(BaseModel):
    """Request body for step endpoint."""
    action: Action


class StateResponse(BaseModel):
    """Response from state endpoint."""
    task_id: str
    step_number: int
    max_steps: int
    done: bool
    score: float
    num_active_rows: int
    action_count: int