# 📘 Complete `docs/SETUP.md` File


# Setup Guide — Data Cleaning OpenEnv

Complete instructions for installing, running, and using the Data Cleaning OpenEnv environment.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Local Installation](#local-installation)
4. [Docker Installation](#docker-installation)
5. [Using the Live Hugging Face Space](#using-the-live-hugging-face-space)
6. [Running the Baseline Agent](#running-the-baseline-agent)
7. [Environment Variables](#environment-variables)
8. [Troubleshooting](#troubleshooting)
9. [Verification](#verification)
10. [Next Steps](#next-steps)

---

## 📦 Prerequisites

Before you begin, ensure you have:

| Software | Minimum Version | Installation |
|----------|----------------|--------------|
| Python | 3.10 or higher | [python.org](https://python.org) |
| Git | 2.0 or higher | [git-scm.com](https://git-scm.com) |
| Docker (optional) | 20.10+ | [docker.com](https://docker.com) |
| pip | Latest | Included with Python |

**Verify installations:**
```bash
python --version    # Should show 3.10+
git --version
docker --version   # Optional
```

---

## 🚀 Quick Start

**Fastest way to try the environment:**

1. **Use the live demo** (no installation):
   ```
   https://kylian07-meta-env-rl.hf.space
   ```

2. **Or run locally in 3 commands:**
   ```bash
   pip install -r requirements.txt
   python main.py
   # Visit http://localhost:7860/docs
   ```

---

## 🖥️ Local Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Kylian07/data-cleaning-openenv.git
cd data-cleaning-openenv
```

### Step 2: Create Virtual Environment

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Start the Server

```bash
python main.py
```

**Expected output:**
```
Starting Data Cleaning OpenEnv server...
INFO:     Uvicorn running on http://0.0.0.0:7860
INFO:     Application startup complete.
```

### Step 5: Verify Installation

Open your browser and visit:
- **Health Check:** http://localhost:7860/
- **API Documentation:** http://localhost:7860/docs

You should see JSON response and interactive Swagger UI.

---

## 🐳 Docker Installation

### Option A: Build from Source

```bash
# Clone repository
git clone https://github.com/Kylian07/data-cleaning-openenv.git
cd data-cleaning-openenv

# Build Docker image
docker build -t data-cleaning-env .

# Run container
docker run -p 7860:7860 data-cleaning-env
```

### Option B: Pull from Registry (if available)

```bash
docker pull kylian07/data-cleaning-env:latest
docker run -p 7860:7860 kylian07/data-cleaning-env:latest
```

### Docker Verification

Visit: http://localhost:7860/docs

---

## 🌐 Using the Live Hugging Face Space

No installation required! Use the deployed environment:

### Base URL
```
https://kylian07-meta-env-rl.hf.space
```

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/tasks` | GET | List available tasks |
| `/reset` | POST | Start new episode |
| `/step` | POST | Take an action |
| `/state` | GET | Get current state |
| `/docs` | GET | Interactive API docs |

### Example cURL Commands

```bash
# Health check
curl https://kylian07-meta-env-rl.hf.space/

# List tasks
curl https://kylian07-meta-env-rl.hf.space/tasks

# Reset with easy task
curl -X POST https://kylian07-meta-env-rl.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_format_standardization"}'

# Take an action
curl -X POST https://kylian07-meta-env-rl.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "fix_cell",
      "row_index": 0,
      "column_name": "name",
      "new_value": "John Doe"
    }
  }'

# Get current state
curl https://kylian07-meta-env-rl.hf.space/state
```

### Python Example

```python
import requests

BASE_URL = "https://kylian07-meta-env-rl.hf.space"

# Reset
response = requests.post(f"{BASE_URL}/reset", 
    json={"task_id": "easy_format_standardization"})
obs = response.json()["observation"]
print(f"Initial score: {obs['current_score']:.2%}")

# Fix a cell
response = requests.post(f"{BASE_URL}/step",
    json={"action": {
        "action_type": "fix_cell",
        "row_index": 0,
        "column_name": "name",
        "new_value": "John Doe"
    }})
result = response.json()
print(f"New score: {result['reward']['score']:.2%}")
```

---

## 🤖 Running the Baseline Agent

The baseline agent uses an LLM (via Hugging Face Inference API) to interact with the environment.

### Step 1: Get Hugging Face Token

1. Go to: https://huggingface.co/settings/tokens
2. Click "New token"
3. Name: `openenv-agent`
4. Type: **Write** (required for inference API)
5. Click "Generate"
6. **Copy** the token (starts with `hf_`)

### Step 2: Set Environment Variables

**Windows (Command Prompt):**
```cmd
set API_BASE_URL=https://router.huggingface.co/cerebras/v1
set MODEL_NAME=llama3.1-8b
set HF_TOKEN=hf_your_token_here
set ENV_URL=http://localhost:7860
```

**Windows (PowerShell):**
```powershell
$env:API_BASE_URL = "https://router.huggingface.co/cerebras/v1"
$env:MODEL_NAME = "llama3.1-8b"
$env:HF_TOKEN = "hf_your_token_here"
$env:ENV_URL = "http://localhost:7860"
```

**macOS/Linux:**
```bash
export API_BASE_URL=https://router.huggingface.co/cerebras/v1
export MODEL_NAME=llama3.1-8b
export HF_TOKEN=hf_your_token_here
export ENV_URL=http://localhost:7860
```

> **Note:** If using the HF Space, set `ENV_URL=https://kylian07-meta-env-rl.hf.space`

### Step 3: Start the Environment

If running locally:
```bash
python main.py
```

If using HF Space, skip this step.

### Step 4: Run the Agent

In a **new terminal** (with environment variables set):

```bash
python inference.py
```

**Expected output:**
```
============================================================
  Data Cleaning OpenEnv — Baseline Inference
  Model:    llama3.1-8b
  API Base: https://router.huggingface.co/cerebras/v1
  Env URL:  http://localhost:7860
============================================================

Waiting for environment to be ready...
Environment is ready!

============================================================
  TASK: easy_format_standardization
============================================================
  Initial score: 4.00%
  Step  1: fix_cell   row=0 col=name val=John Doe
           Score: 8.00% (delta: +0.0400)
  ...
```

---

## 🔧 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `API_BASE_URL` | Yes | LLM API endpoint | `https://router.huggingface.co/cerebras/v1` |
| `MODEL_NAME` | Yes | Model identifier | `llama3.1-8b` |
| `HF_TOKEN` | Yes | HuggingFace token with Write access | `hf_xxxxx` |
| `ENV_URL` | Yes | Environment server URL | `http://localhost:7860` |

**Default values** (used if not set):
- `API_BASE_URL`: `https://router.huggingface.co/cerebras/v1`
- `MODEL_NAME`: `llama3.1-8b`
- `ENV_URL`: `http://localhost:7860`

---

## 🐛 Troubleshooting

### Port 7860 Already in Use

**Problem:** `OSError: [Errno 48] Address already in use`

**Solution:**
```bash
# Find process using port 7860
# Windows:
netstat -ano | findstr :7860
taskkill /PID <process_id> /F

# macOS/Linux:
lsof -i :7860
kill -9 <process_id>

# Or use a different port:
python main.py --port 8000
```

### Docker Issues

**"Docker daemon not running":**
- Start Docker Desktop from Start Menu (Windows) or Applications (Mac)
- Wait for the whale icon to be steady (not loading)

**"Permission denied" on Linux:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### LLM API Errors

**401 Unauthorized:**
- Token is invalid or expired
- Create new token at https://huggingface.co/settings/tokens
- Ensure token has **Write** permission (not just Read)

**402 Payment Required:**
- Free credits exhausted
- Wait for monthly reset OR use a different model
- Try: `mistralai/Mistral-7B-Instruct-v0.3` (also free via Cerebras)

**404 Not Found:**
- Model name is wrong
- For Cerebras, use: `llama3.1-8b` (exactly)
- Check available models: https://huggingface.co/cerebras

**429 Rate Limited:**
- Too many requests
- Add delays between API calls
- Wait a few minutes and retry

### Import Errors

**"No module named 'fastapi'":**
```bash
pip install -r requirements.txt
# Or install individually:
pip install fastapi uvicorn pydantic openai requests
```

**"ModuleNotFoundError" after moving files:**
- Ensure you're in the correct directory
- Check that all `.py` files are in the same folder
- Reinstall: `pip install -r requirements.txt`

### Virtual Environment Issues

**"(venv)" not showing:**
```cmd
# Windows cmd:
venv\Scripts\activate

# Windows PowerShell:
venv\Scripts\Activate.ps1
# If blocked: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# macOS/Linux:
source venv/bin/activate
```

---

## ✅ Verification

### Test 1: Server Health

```bash
curl http://localhost:7860/
```

**Expected:**
```json
{
  "status": "ok",
  "environment": "data-cleaning-env",
  "version": "1.0.0",
  "tasks": ["easy_format_standardization", "medium_dedup_and_fill", "hard_full_pipeline"]
}
```

### Test 2: Reset Endpoint

```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_format_standardization"}'
```

**Expected:** JSON with `observation`, `reward`, `done: false`

### Test 3: Step Endpoint

```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "fix_cell",
      "row_index": 0,
      "column_name": "name",
      "new_value": "John Doe"
    }
  }'
```

**Expected:** JSON with updated `observation`, `reward` (score increased), `done: false`

### Test 4: Interactive Docs

Open: http://localhost:7860/docs

You should see the Swagger UI with all endpoints.

---

## 📊 Test Scripts

### Quick Test (test_api.py)

Create `test_api.py`:

```python
"""Quick test of all endpoints."""
import requests

BASE = "http://localhost:7860"

print("Testing Data Cleaning OpenEnv...")

# 1. Health
r = requests.get(f"{BASE}/")
print(f"1. Health: {r.status_code} {r.json()['status']}")

# 2. Tasks
r = requests.get(f"{BASE}/tasks")
print(f"2. Tasks: {r.status_code} {len(r.json()['tasks'])} tasks")

# 3. Reset
r = requests.post(f"{BASE}/reset", 
    json={"task_id": "easy_format_standardization"})
obs = r.json()['observation']
print(f"3. Reset: {r.status_code} Score={obs['current_score']:.2%}")

# 4. Step
r = requests.post(f"{BASE}/step",
    json={"action": {"action_type": "fix_cell", "row_index": 0, 
                     "column_name": "name", "new_value": "John Doe"}})
reward = r.json()['reward']
print(f"4. Step: {r.status_code} Score={reward['score']:.2%} Δ={reward['delta']:+.4f}")

# 5. State
r = requests.get(f"{BASE}/state")
state = r.json()
print(f"5. State: {r.status_code} Step={state['step_number']}/{state['max_steps']}")

print("\n✅ All endpoints working!")
```

Run:
```bash
python test_api.py
```

---

## 🎯 Next Steps

After setup:

1. **Explore the tasks:**
   - Try `easy_format_standardization` first
   - Progress to `medium_dedup_and_fill`
   - Challenge yourself with `hard_full_pipeline`

2. **Build your own agent:**
   - Modify `inference.py` with better prompting
   - Try different LLMs (GPT-4, Claude, etc.)
   - Implement rule-based agents

3. **Experiment:**
   - Add new tasks in `tasks.py`
   - Modify scoring in `graders.py`
   - Add new action types

4. **Deploy:**
   - Deploy to Hugging Face Spaces (see `docs/SUBMISSION.md`)
   - Share with the community

---

## 📚 Additional Resources

| Resource | Link |
|----------|------|
| OpenEnv Specification | https://github.com/opendevenv/spec |
| FastAPI Documentation | https://fastapi.tiangolo.com |
| Hugging Face Inference API | https://huggingface.co/docs/api-inference |
| Docker Documentation | https://docs.docker.com |
| Pydantic Documentation | https://docs.pydantic.dev |

---

## 🆘 Getting Help

1. **Check this guide's Troubleshooting section**
2. **Review the logs** — error messages are usually descriptive
3. **Open an Issue** on GitHub: https://github.com/Kylian07/data-cleaning-openenv/issues
4. **Ask in competition Discord/Slack** (if available)

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](../LICENSE) file.

---

**Last updated:** 2024-01-15  
**Environment version:** 1.0.0  
**Compatible with:** OpenEnv spec v0.1+
```

---

## 📌 How to Use This File

1. **Create the file:**
   ```cmd
   notepad docs\SETUP.md
   ```

2. **Copy and paste** the entire content above

3. **Save** the file

4. **Update the links** (replace `Kylian07` with your actual GitHub username if different)

5. **Commit and push:**
   ```cmd
   git add docs/SETUP.md
   git commit -m "Add comprehensive SETUP.md"
   git push
   ```

---

This `SETUP.md` is **production-ready** and covers:
- ✅ Complete installation instructions (local + Docker)
- ✅ Live HF Space usage
- ✅ Baseline agent setup
- ✅ Environment variables reference
- ✅ Troubleshooting common issues
- ✅ Verification tests
- ✅ Next steps for users

**Would you like me to create the `ARCHITECTURE.md` file next, or do you have questions about `SETUP.md`?** 🚀
