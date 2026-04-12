"""
FastAPI server — serves the Data Cleaning OpenEnv.

Endpoints:
  GET  /       → Health check (must return 200)
  GET  /tasks  → List available tasks
  POST /reset  → Start new episode
  POST /step   → Take an action
  GET  /state  → Get current state
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    StepResult, ResetRequest, StepRequest, StateResponse
)
from environment import DataCleaningEnv
from tasks import list_tasks

# ── Create the FastAPI app ────────────────────────────────
app = FastAPI(
    title="Data Cleaning OpenEnv",
    description=(
        "An OpenEnv environment for training AI agents "
        "on real-world tabular data cleaning tasks."
    ),
    version="1.0.0",
)

# Allow requests from anywhere (needed for HF Spaces)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Create the environment instance ───────────────────────
env = DataCleaningEnv()


# ══════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════

@app.get("/")
def health():
    """
    Health check endpoint.
    The validator pings this — must return 200.
    """
    return {
        "status": "ok",
        "environment": "data-cleaning-env",
        "version": "1.0.0",
        "tasks": list_tasks()
    }


@app.get("/tasks")
def get_tasks():
    """List all available tasks."""
    return {"tasks": list_tasks()}


@app.post("/reset", response_model=StepResult)
def reset(req: ResetRequest):
    """
    Reset the environment and start a new episode.
    
    Body: {"task_id": "easy_format_standardization"}
    """
    try:
        result = env.reset(task_id=req.task_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResult)
def step(req: StepRequest):
    """
    Take one action in the environment.
    
    Body: {"action": {"action_type": "fix_cell", "row_index": 0, ...}}
    """
    result = env.step(req.action)
    return result


@app.get("/state", response_model=StateResponse)
def state():
    """Get current environment state summary."""
    return env.state()


# ── Run the server ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("Starting Data Cleaning OpenEnv server...")
    print("Docs available at: http://localhost:7860/docs")
    uvicorn.run(app, host="0.0.0.0", port=7860)