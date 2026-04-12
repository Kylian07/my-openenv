# OpenEnv Submission — Data Cleaning Environment

## Team/Author
- Name: Rajdeep Pal, Jotiraditya Banerjee, Sampurna Sarkar
- Team Name : CodeFuse
- HF Username: Kylian07

## Deployment URLs

**Hugging Face Space:**
https://huggingface.co/spaces/Kylian07/Meta_env_rl

**API Endpoints:**
- Health: https://kylian07-meta-env-rl.hf.space/
- Docs: https://kylian07-meta-env-rl.hf.space/docs
- Reset: https://kylian07-meta-env-rl.hf.space/reset
- Step: https://kylian07-meta-env-rl.hf.space/step
- State: https://kylian07-meta-env-rl.hf.space/state

## Environment Details

**Name:** Data Cleaning OpenEnv  
**Domain:** Tabular data cleaning (real-world task)  
**Description:** An environment where AI agents learn to clean messy datasets by fixing formatting, removing duplicates, filling missing values, and detecting outliers.

### Tasks (3 difficulty levels)

1. **easy_format_standardization** (5 rows, 35 steps)
   - Fix formatting issues only
   - Expected score: 85-95%

2. **medium_dedup_and_fill** (10 rows, 60 steps)
   - Formatting + duplicates + missing values
   - Expected score: 65-80%

3. **hard_full_pipeline** (15 rows, 100 steps)
   - All above + outliers + cross-field validation
   - Expected score: 45-65%

### Action Space

- `fix_cell`: Change a cell value
- `delete_row`: Remove duplicate/invalid row
- `submit`: Submit cleaned dataset for grading

### Reward Design

- Continuous scoring (0.0 to 1.0)
- Per-step delta feedback
- Partial credit for each correct cell
- Invalid action penalty: -0.01

### Baseline Results

Using Llama 3.1-8B via Cerebras:
- Easy: 44%
- Medium: 38%
- Hard: 39%

(Note: Free API credits limited during testing)

## Technical Details

**Files included:**
- ✅ models.py (Pydantic typed models)
- ✅ tasks.py (3 tasks with ground truth)
- ✅ graders.py (deterministic scoring)
- ✅ environment.py (reset/step/state)
- ✅ main.py (FastAPI server)
- ✅ inference.py (baseline agent)
- ✅ openenv.yaml (metadata)
- ✅ Dockerfile (containerization)
- ✅ README.md (documentation)

**OpenEnv Compliance:**
- ✅ Typed Observation/Action/Reward models
- ✅ step() returns observation, reward, done, info
- ✅ reset() returns initial observation
- ✅ state() returns current state
- ✅ Deployed via Docker on HF Spaces
- ✅ All endpoints respond correctly

**Testing:**
```bash
# Health check
curl https://kylian07-meta-env-rl.hf.space/

# Reset environment
curl -X POST https://kylian07-meta-env-rl.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_format_standardization"}'

# Take action
curl -X POST https://kylian07-meta-env-rl.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "fix_cell", "row_index": 0, "column_name": "name", "new_value": "John Doe"}}'