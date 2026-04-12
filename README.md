# Data Cleaning OpenEnv

An OpenEnv-compliant environment where AI agents must clean messy tabular datasets:
fixing formatting, removing duplicates, filling missing values, and detecting outliers.

**HF Space:** https://huggingface.co/spaces/Kylian07/my-env

**Live API:** https://kylian07-my-env.hf.space

**API Docs:** https://kylian07-my-env.hf.space/docs

---

## Quick Start

```bash
pip install -r requirements.txt
cd src
uvicorn main:app --host 0.0.0.0 --port 7860
```

API is now live at http://localhost:7860/docs

---

## Environment Variables

These **must** be set before running `inference.py`:

| Variable | Description | Example |
|----------|-------------|---------|
| `API_BASE_URL` | LLM API endpoint | `https://router.huggingface.co/cerebras/v1` |
| `MODEL_NAME` | Model identifier | `llama3.1-8b` |
| `HF_TOKEN` | Hugging Face / API key | `hf_xxxxx` |
| `ENV_URL` | Environment server URL | `http://localhost:7860` |

**Windows CMD:**
```cmd
set API_BASE_URL=https://router.huggingface.co/cerebras/v1
set MODEL_NAME=llama3.1-8b
set HF_TOKEN=hf_your_token_here
set ENV_URL=http://localhost:7860
```

**Windows PowerShell:**
```powershell
$env:API_BASE_URL = "https://router.huggingface.co/cerebras/v1"
$env:MODEL_NAME   = "llama3.1-8b"
$env:HF_TOKEN     = "hf_your_token_here"
$env:ENV_URL      = "http://localhost:7860"
```

**Linux / macOS:**
```bash
export API_BASE_URL=https://router.huggingface.co/cerebras/v1
export MODEL_NAME=llama3.1-8b
export HF_TOKEN=hf_your_token_here
export ENV_URL=http://localhost:7860
```

---

## Pre-Submission Validation

Run the validator **before submitting** to ensure all checklist gates pass:

```bash
# (with environment server running on port 7860)
python validate.py
```

Against the live HF Space:
```bash
set ENV_URL=https://kylian07-my-env.hf.space
python validate.py
```

---

## Running the Inference Script

```bash
# 1. Start the server (in one terminal)
cd src
uvicorn main:app --host 0.0.0.0 --port 7860

# 2. Set env vars and run inference (in another terminal)
set API_BASE_URL=https://router.huggingface.co/cerebras/v1
set MODEL_NAME=llama3.1-8b
set HF_TOKEN=hf_your_token_here
set ENV_URL=http://localhost:7860
python inference.py
```

Expected output format:
```
[START] {"task_id": "easy_format_standardization", "model": "llama3.1-8b", ...}
[STEP]  {"step": 1, "action": {...}, "reward": 0.04, "score": 0.08, "done": false}
...
[END]   {"task_id": "easy_format_standardization", "final_score": 0.84, "steps": 21}
```

---

## Tasks

| Task ID | Difficulty | Rows | Max Steps | Description |
|---------|----------|------|-----------|-------------|
| `easy_format_standardization` | Easy | 5 | 35 | Fix formatting only |
| `medium_dedup_and_fill` | Medium | 10 | 60 | Format + duplicates + missing values |
| `hard_full_pipeline` | Hard | 15 | 100 | All above + outliers + cross-field validation |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check (returns 200) |
| `GET` | `/tasks` | List available tasks |
| `POST` | `/reset` | Start a new episode |
| `POST` | `/step` | Take an action |
| `GET` | `/state` | Get current environment state |

---

## Project Structure

```
my-openenv-main/
├── inference.py         ← Baseline inference script (mandatory at root)
├── validate.py          ← Pre-submission validator
├── Dockerfile           ← Container build for HF Spaces
├── openenv.yaml         ← OpenEnv specification
├── requirements.txt     ← Python dependencies
├── README.md            ← This file
└── src/
    ├── main.py          ← FastAPI server (uvicorn entry point)
    ├── environment.py   ← reset() / step() / state() logic
    ├── models.py        ← Pydantic typed models
    ├── tasks.py         ← Task definitions with ground truth
    └── graders.py       ← Deterministic scoring (0.0–1.0)
```

---

## License

MIT License — see [LICENSE.txt](LICENSE.txt)
