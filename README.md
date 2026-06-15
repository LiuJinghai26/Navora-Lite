# Navora Lite

[中文文档](./README.zh-CN.md)

Navora Lite is a chat-first browser Agent Dashboard. It lets a user create browser automation runs, watch the live run state, review screenshots and timeline steps, and inspect structured extraction output from one local workspace.

## Technical Documentation

- [Technical Report (English)](./docs/TECHNICAL.md)
- [技术报告（中文）](./docs/TECHNICAL.zh-CN.md)

## What You Get

- Chat-first task entry through New Chat.
- Tasks dashboard with preset website demos, history search, status filters, and local history deletion.
- Run detail page with Chat Panel, Run Header, Browser Preview, Execution Timeline, Recording, Output, Inputs, and Code tabs.
- FastAPI backend with runs, tasks, settings, and SSE event APIs.
- Playwright Chromium execution for real browser tasks.
- OpenAI-compatible model configuration for hosted or local model endpoints.
- Local JSON run storage and screenshot artifacts.
- CLI scripts for starting, stopping, and exporting runs.

## Current Behavior

- Preset tasks can run without a model API because their action plans are built into the backend.
- Free-form browser tasks require model settings before they can auto-start.
- `BROWSER_HEADLESS=true` runs Chromium without a visible window; `BROWSER_HEADLESS=false` opens a visible browser, detaches control after the run, and keeps the browser open for inspection.
- The old local mock shopping page is disabled and no longer exposed as `/mock/findparts`.
- If Playwright or Chromium cannot launch, the run fails with an execution error. Install Chromium with Playwright before running browser tasks.

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
  scripts/        Run, stop, and export CLI scripts
  docs/           Technical documentation
  README.md
  README.zh-CN.md
  .env.example
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
http://localhost:3000/new-chat
```

To run without model configuration, open:

```text
http://localhost:3000/tasks
```

Then start one of the preset website demos.

### 4. Configure a Model for Free-Form Tasks

Open Settings in the app or edit:

```text
apps/server/.env
```

For OpenAI-compatible endpoints:

```env
MODEL_PROVIDER=openai-compatible
MODEL_NAME=qwen3-32b
API_BASE=http://localhost:8001/v1
API_KEY=your-api-key
MAX_TOKENS=4096
TEMPERATURE=0.2
```

For local providers, the API key can be empty:

```env
MODEL_PROVIDER=ollama
MODEL_NAME=qwen3:latest
API_BASE=http://localhost:11434/v1
API_KEY=
```

After saving settings through the UI, the backend writes `apps/server/.env` and refreshes the cached settings.

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
http://localhost:3000/new-chat
```

For a model-free smoke test, open `http://localhost:3000/tasks` and run a preset task.

## CLI Commands

The CLI talks to the same backend API as the web UI. Because `run_demo.py` creates a free-form run, configure a model first.

Run a task:

```bash
python scripts/run_demo.py --task "Open Hacker News and extract the current top story with its source, score, age, and comments." --url "https://news.ycombinator.com/"
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

## API Reference

Create run:

```http
POST /api/runs
```

List runs:

```http
GET /api/runs
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

Task history:

```http
GET /api/tasks
DELETE /api/tasks/{run_id}
```

Settings:

```http
GET /api/settings
POST /api/settings
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

### Free-Form Tasks Require Model Settings

If New Chat shows:

```text
请先在 Settings 中配置模型 API，再启动浏览器任务。
```

open Settings and configure an OpenAI-compatible `/v1` endpoint, or run a preset task from the Tasks page.

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

### Browser Opens `localhost:3000`, but the App Fails or Shows `missing required error components`

If Next.js reports:

```text
Port 3000 is in use, trying 3001 instead.
Local: http://localhost:3001
```

open the port printed by the current dev server, for example:

```text
http://localhost:3001/new-chat
```

PowerShell cleanup if you want to use `3000` again:

```powershell
Get-NetTCPConnection -LocalPort 3000,3001 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

cd "E:\codex\Navora Lite\navora-lite\apps\web"
pnpm.cmd dev
```

### `pnpm approve-builds` Fails in PowerShell

If `pnpm approve-builds` fails because PowerShell blocks `pnpm.ps1`, call the `.cmd` launcher:

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\web"
pnpm.cmd approve-builds
```

## Notes

- `docker-compose.yml` is optional and only starts the backend service.
- The backend stores runs in `apps/server/data/runs.json` and screenshots in `apps/server/data/artifacts`.
- Safety guards block high-risk actions such as payment, order submission, password changes, account deletion, captcha bypass, and sensitive uploads.
