# Navora Lite

[中文文档](./README.zh-CN.md)

Navora Lite is a chat-first browser Agent Dashboard. It lets a user start a browser automation run from a central chat panel, then watch the browser preview, timeline, screenshots, and extracted JSON update in real time.

The default demo does not require a real model service. If no model endpoint is configured, the backend automatically uses the mock planner and runs the local mock commerce flow.

## What You Get

- Chat-first dashboard with the Chat Panel above the tabs.
- Sidebar, Run Header, Overview, Output, Inputs, Recording, and Code tabs.
- Browser Preview with fullscreen mode, Controlling status, and Stop Controlling.
- FastAPI backend with runs API, settings API, mock commerce page, and SSE events.
- Playwright browser execution with a mock browser fallback.
- OpenAI-compatible model configuration for API key and local model endpoints.
- CLI scripts for running the demo, stopping a run, and exporting run logs.

## Requirements

- Python 3.10 or newer.
- Node.js 18 or newer.
- pnpm.
- Chromium installed through Playwright.

Check versions:

```bash
python --version
node --version
pnpm --version
```

On Windows PowerShell, if `pnpm` is blocked by execution policy, use `pnpm.cmd` instead.

## Project Structure

```text
navora-lite/
  apps/
    server/       FastAPI backend
    web/          Next.js frontend
  scripts/        Demo, stop, and export CLI scripts
  docs/           Technical documentation
  README.md
  README.zh-CN.md
  .env.example
```

Generated visual asset:

```text
apps/web/public/assets/browser-preview-placeholder.png
```

## Quick Start: Bash

Use these commands on macOS, Linux, Git Bash, WSL, or another Bash-like shell.

### 1. Prepare Environment Files

```bash
cd navora-lite
cp .env.example apps/server/.env
cp apps/web/.env.example apps/web/.env.local
```

### 2. Start Backend

Run this in terminal 1:

```bash
cd navora-lite/apps/server
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Optional backend startup without a virtual environment:

```bash
cd navora-lite/apps/server
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

This is faster for quick demos, but it installs dependencies into the active Python environment. If you already use Python for other projects, the virtual environment flow is safer.

Backend health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","app":"navora-lite"}
```

### 3. Start Frontend

Run this in terminal 2:

```bash
cd navora-lite/apps/web
pnpm install
pnpm dev
```

Open:

```text
http://localhost:3000/runs/demo
```

### 4. Run Demo CLI

Run this in terminal 3 after the backend is running:

```bash
cd navora-lite
python scripts/run_demo.py \
  --task "Find the AURORA TASK LAMP, choose Warm White, set quantity to 2, add it to the cart, and extract the cart summary" \
  --url "http://localhost:8000/mock/findparts"
```

Expected final result:

```json
{
  "status": "completed",
  "extracted": {
    "product_name": "AURORA TASK LAMP",
    "color": "Warm White",
    "quantity": 2,
    "subtotal": "$178"
  }
}
```

## Quick Start: Windows PowerShell

Use these commands in PowerShell. This flow avoids activating the Python virtual environment, so it also works when script execution policy blocks `Activate.ps1`.

### 1. Prepare Environment Files

```powershell
cd navora-lite
Copy-Item .env.example apps/server/.env -Force
Copy-Item apps/web/.env.example apps/web/.env.local -Force
```

### 2. Start Backend

Run this in PowerShell window 1:

```powershell
cd navora-lite/apps/server
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Optional backend startup without a virtual environment:

```powershell
cd navora-lite/apps/server
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

This is faster for quick demos, but it installs dependencies into the active Python environment. If you already use Python for other projects, the virtual environment flow is safer.

Backend health check:

```powershell
curl.exe http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","app":"navora-lite"}
```

### 3. Start Frontend

Run this in PowerShell window 2:

```powershell
cd navora-lite/apps/web
pnpm.cmd install
pnpm.cmd dev
```

Open:

```text
http://localhost:3000/runs/demo
```

### 4. Run Demo CLI

Run this in PowerShell window 3 after the backend is running:

```powershell
cd navora-lite
python scripts/run_demo.py `
  --task "Find the AURORA TASK LAMP, choose Warm White, set quantity to 2, add it to the cart, and extract the cart summary" `
  --url "http://localhost:8000/mock/findparts"
```

Expected final result:

```json
{
  "status": "completed",
  "extracted": {
    "product_name": "AURORA TASK LAMP",
    "color": "Warm White",
    "quantity": 2,
    "subtotal": "$178"
  }
}
```

## CLI Commands

Run demo:

```bash
python scripts/run_demo.py --task "Find the AURORA TASK LAMP, choose Warm White, set quantity to 2, add it to the cart, and extract the cart summary" --url "http://localhost:8000/mock/findparts"
```

Stop a run:

```bash
python scripts/stop_run.py --run-id run_xxxxxxxxxxxxxxxxxx
```

Export a run:

```bash
python scripts/export_run.py --run-id run_xxxxxxxxxxxxxxxxxx --output ./exports/run.json
```

## Testing and Build

Bash:

```bash
cd navora-lite/apps/server
source .venv/bin/activate
python -m pytest

cd ../web
pnpm build
```

Windows PowerShell:

```powershell
cd navora-lite/apps/server
.\.venv\Scripts\python.exe -m pytest

cd ..\web
pnpm.cmd build
```

Without a virtual environment:

```bash
cd navora-lite/apps/server
python -m pytest
```

```powershell
cd navora-lite/apps/server
python -m pytest
```

## Model Configuration

Edit `apps/server/.env`.

OpenAI-compatible API:

```env
MODEL_PROVIDER=openai-compatible
MODEL_NAME=qwen3-32b
API_BASE=http://localhost:8001/v1
API_KEY=your-api-key
MAX_TOKENS=4096
TEMPERATURE=0.2
```

Ollama:

```env
MODEL_PROVIDER=ollama
MODEL_NAME=qwen3:latest
API_BASE=http://localhost:11434/v1
API_KEY=
```

LM Studio:

```env
MODEL_PROVIDER=lmstudio
MODEL_NAME=qwen3-4bit
API_BASE=http://localhost:1234/v1
API_KEY=
```

vLLM:

```env
MODEL_PROVIDER=vllm
MODEL_NAME=Qwen/Qwen3-32B
API_BASE=http://localhost:8001/v1
API_KEY=
```

If the model call fails, times out, returns invalid JSON, or no endpoint is configured, Navora Lite automatically falls back to the mock planner.

## API Reference

Create run:

```http
POST /api/runs
```

Get run:

```http
GET /api/runs/{run_id}
```

Stop run:

```http
POST /api/runs/{run_id}/stop
```

Rerun:

```http
POST /api/runs/{run_id}/rerun
```

SSE events:

```http
GET /api/runs/{run_id}/events
```

Mock commerce page:

```http
GET /mock/findparts
```

## Troubleshooting

### `pnpm.ps1 cannot be loaded`

Use `pnpm.cmd` in PowerShell:

```powershell
pnpm.cmd install
pnpm.cmd dev
```

### Playwright Cannot Launch Chromium

Install Chromium:

```bash
python -m playwright install chromium
```

If Chromium still cannot launch, the backend falls back to a mock browser and writes SVG screenshots so the demo can continue.

### Install Backend Dependencies Without a Virtual Environment

For quick demos:

```bash
cd navora-lite/apps/server
python -m pip install -r requirements.txt
```

Use a virtual environment if global dependency conflicts appear.

### Port Already in Use

Backend alternative port:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Frontend alternative port:

```bash
pnpm dev -- -p 3001
```

PowerShell frontend alternative:

```powershell
pnpm.cmd exec next dev -p 3001
```

### No Model Configured

This is expected for the default demo. The backend uses the mock planner and still completes the Aurora lamp cart-summary task.

## Notes

- `docker-compose.yml` is optional and not required for the local MVP workflow.
- Architecture, API, run lifecycle, Agent execution details, and extension notes are documented in [docs/TECHNICAL.zh-CN.md](./docs/TECHNICAL.zh-CN.md).
- The mock commerce page has a Checkout button, but the agent intentionally does not use it.
- Safety guards block high-risk actions such as payment, order submission, password changes, account deletion, captcha bypass, and sensitive uploads.

## Startup and Install Troubleshooting

These are common issues seen during local startup.

### Browser Opens `localhost:3000`, but the App Fails or Shows `missing required error components`

Symptom:

```text
Port 3000 is in use, trying 3001 instead.
Local: http://localhost:3001
```

Cause:

Another old Next.js / Node process is already using port `3000`, so the new frontend starts on `3001`. If you still open `http://localhost:3000/runs/demo`, you are visiting the old process, not the frontend you just started.

Quick fix:

```text
http://localhost:3001/runs/demo
```

PowerShell cleanup if you want to use `3000` again:

```powershell
Get-NetTCPConnection -LocalPort 3000,3001 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

cd "E:\codex\Navora Lite\navora-lite\apps\web"
pnpm.cmd dev
```

After restart, open:

```text
http://localhost:3000/runs/demo
```

### `pnpm approve-builds` Fails in PowerShell

Symptom:

```text
Ignored build scripts: unrs-resolver@...
Run "pnpm approve-builds" to pick which dependencies should be allowed to run scripts.
```

Then this command fails:

```powershell
pnpm approve-builds
```

with:

```text
pnpm.ps1 cannot be loaded because running scripts is disabled on this system.
```

Cause:

PowerShell blocks the `pnpm.ps1` script because of the local execution policy. The install warning itself is usually not fatal, but if you want to approve the package build script, call the `.cmd` launcher instead.

Fix:

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\web"
pnpm.cmd approve-builds
```

In the prompt, select `unrs-resolver`, approve it, and let pnpm run the postinstall script. You can also continue using `pnpm.cmd` for normal frontend commands:

```powershell
pnpm.cmd install
pnpm.cmd dev
pnpm.cmd build
```
