# Navora Lite

[English README](./README.md)

Navora Lite 是一个以聊天为核心入口的轻量版浏览器 Agent Dashboard。用户可以在主界面的 Chat Panel 输入自然语言任务，系统会创建 run、规划浏览器动作、执行 mock 电商流程，并实时展示浏览器预览、执行时间线、截图记录和结构化 JSON 提取结果。

默认 demo 不需要真实模型服务。没有配置模型 endpoint 或 API Key 时，后端会自动使用 mock planner，仍然可以完整跑通本地 mock 电商任务。

## 功能特性

- Chat-first 运行页面：主 Chat Panel 位于 Header 下方、Tabs 上方。
- Runs Dashboard：包含 Sidebar、Run Header、Overview、Output、Inputs、Recording、Code。
- Browser Preview：支持截图预览、全屏查看、Controlling 状态和 Stop Controlling。
- FastAPI 后端：支持 runs API、settings API、本地 mock 电商页和 SSE 实时事件。
- Playwright 执行：优先使用 Chromium；当 Playwright 或浏览器不可用时，自动切换到 mock browser fallback。
- 模型接入：支持 API Key、本地模型 endpoint、OpenAI-compatible 接口。
- CLI 脚本：支持运行 demo、停止 run、导出 run 日志。

## 环境要求

- Python 3.10 或更新版本。
- Node.js 18 或更新版本。
- pnpm。
- Playwright Chromium。

检查版本：

```bash
python --version
node --version
pnpm --version
```

Windows PowerShell 如果提示 `pnpm.ps1 cannot be loaded`，请使用 `pnpm.cmd`。

## 项目结构

```text
navora-lite/
  apps/
    server/       FastAPI 后端
    web/          Next.js 前端
  scripts/        demo、stop、export CLI 脚本
  docs/           技术文档
  README.md
  README.zh-CN.md
  .env.example
```

生成的浏览器预览占位图：

```text
apps/web/public/assets/browser-preview-placeholder.png
```

## Bash 完整启动流程

适用于 macOS、Linux、Git Bash、WSL 或其他 Bash-like shell。

### 1. 准备环境变量文件

```bash
cd navora-lite
cp .env.example apps/server/.env
cp apps/web/.env.example apps/web/.env.local
```

### 2. 启动后端

在终端 1 执行：

```bash
cd navora-lite/apps/server
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

可选：不使用虚拟环境启动后端：

```bash
cd navora-lite/apps/server
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

这种方式适合快速演示，但依赖会安装到当前 Python 环境中。如果你同时维护多个 Python 项目，虚拟环境方式更稳妥。

后端健康检查：

```bash
curl http://localhost:8000/health
```

期望返回：

```json
{"status":"ok","app":"navora-lite"}
```

### 3. 启动前端

在终端 2 执行：

```bash
cd navora-lite/apps/web
pnpm install
pnpm dev
```

打开页面：

```text
http://localhost:3000/runs/demo
```

### 4. 运行 demo CLI

后端启动后，在终端 3 执行：

```bash
cd navora-lite
python scripts/run_demo.py \
  --task "Add FIRESTONE W01-377-8537 to the cart and set quantity to 1" \
  --url "http://localhost:8000/mock/findparts"
```

期望最终结果：

```json
{
  "status": "completed",
  "extracted": {
    "product_name": "FIRESTONE W01-377-8537",
    "quantity": 1
  }
}
```

## Windows PowerShell 完整启动流程

下面的命令不依赖 `Activate.ps1`，即使 PowerShell 执行策略阻止虚拟环境激活，也可以运行。

### 1. 准备环境变量文件

```powershell
cd navora-lite
Copy-Item .env.example apps/server/.env -Force
Copy-Item apps/web/.env.example apps/web/.env.local -Force
```

### 2. 启动后端

在 PowerShell 窗口 1 执行：

```powershell
cd navora-lite/apps/server
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

可选：不使用虚拟环境启动后端：

```powershell
cd navora-lite/apps/server
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

这种方式适合快速演示，但依赖会安装到当前 Python 环境中。如果你同时维护多个 Python 项目，虚拟环境方式更稳妥。

后端健康检查：

```powershell
curl.exe http://localhost:8000/health
```

期望返回：

```json
{"status":"ok","app":"navora-lite"}
```

### 3. 启动前端

在 PowerShell 窗口 2 执行：

```powershell
cd navora-lite/apps/web
pnpm.cmd install
pnpm.cmd dev
```

打开页面：

```text
http://localhost:3000/runs/demo
```

### 4. 运行 demo CLI

后端启动后，在 PowerShell 窗口 3 执行：

```powershell
cd navora-lite
python scripts/run_demo.py `
  --task "Add FIRESTONE W01-377-8537 to the cart and set quantity to 1" `
  --url "http://localhost:8000/mock/findparts"
```

期望最终结果：

```json
{
  "status": "completed",
  "extracted": {
    "product_name": "FIRESTONE W01-377-8537",
    "quantity": 1
  }
}
```

## CLI 命令

运行 demo：

```bash
python scripts/run_demo.py --task "Add FIRESTONE W01-377-8537 to the cart and set quantity to 1" --url "http://localhost:8000/mock/findparts"
```

停止 run：

```bash
python scripts/stop_run.py --run-id run_xxxxxxxxxxxxxxxxxx
```

导出 run 日志：

```bash
python scripts/export_run.py --run-id run_xxxxxxxxxxxxxxxxxx --output ./exports/run.json
```

## 测试与构建

Bash：

```bash
cd navora-lite/apps/server
source .venv/bin/activate
python -m pytest

cd ../web
pnpm build
```

Windows PowerShell：

```powershell
cd navora-lite/apps/server
.\.venv\Scripts\python.exe -m pytest

cd ..\web
pnpm.cmd build
```

不使用虚拟环境时：

```bash
cd navora-lite/apps/server
python -m pytest
```

```powershell
cd navora-lite/apps/server
python -m pytest
```

## 模型配置

编辑后端环境变量文件：

```text
apps/server/.env
```

OpenAI-compatible API：

```env
MODEL_PROVIDER=openai-compatible
MODEL_NAME=qwen3-32b
API_BASE=http://localhost:8001/v1
API_KEY=your-api-key
MAX_TOKENS=4096
TEMPERATURE=0.2
```

Ollama：

```env
MODEL_PROVIDER=ollama
MODEL_NAME=qwen3:latest
API_BASE=http://localhost:11434/v1
API_KEY=
```

LM Studio：

```env
MODEL_PROVIDER=lmstudio
MODEL_NAME=qwen3-4bit
API_BASE=http://localhost:1234/v1
API_KEY=
```

vLLM：

```env
MODEL_PROVIDER=vllm
MODEL_NAME=Qwen/Qwen3-32B
API_BASE=http://localhost:8001/v1
API_KEY=
```

如果模型不可用、请求超时、返回非 JSON，或没有配置 endpoint，Navora Lite 会自动 fallback 到 mock planner。

## API 速查

创建 run：

```http
POST /api/runs
```

获取 run：

```http
GET /api/runs/{run_id}
```

停止 run：

```http
POST /api/runs/{run_id}/stop
```

重新运行：

```http
POST /api/runs/{run_id}/rerun
```

SSE 实时事件：

```http
GET /api/runs/{run_id}/events
```

mock 电商页面：

```http
GET /mock/findparts
```

## 常见问题

### `pnpm.ps1 cannot be loaded`

PowerShell 执行策略可能会阻止 `pnpm.ps1`。直接使用：

```powershell
pnpm.cmd install
pnpm.cmd dev
```

### Playwright 无法启动 Chromium

先安装 Chromium：

```bash
python -m playwright install chromium
```

如果仍然无法启动，后端会自动切换到 mock browser，并生成 SVG 截图，demo 仍然可以完成。

### 不使用虚拟环境安装后端依赖

快速演示可以直接安装到当前 Python 环境：

```bash
cd navora-lite/apps/server
python -m pip install -r requirements.txt
```

如果出现全局依赖冲突，建议回到虚拟环境方式。

### 端口被占用

后端换端口：

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

前端换端口：

```bash
pnpm dev -- -p 3001
```

PowerShell 前端换端口：

```powershell
pnpm.cmd exec next dev -p 3001
```

### 没有模型配置时能运行吗？

可以。默认 demo 会使用 mock planner，完成 FIRESTONE 商品数量提取任务。

## 说明

- `docker-compose.yml` 是可选增强项，本地 MVP 不依赖 Docker。
- 技术架构、API、run 生命周期、Agent 执行流和扩展指南见 [docs/TECHNICAL.zh-CN.md](./docs/TECHNICAL.zh-CN.md)。
- mock 电商页有 Checkout 按钮，但 Agent 不会自动点击。
- safety guard 会拦截支付、提交订单、删除账号、修改密码、绕过验证码、上传敏感文件等高风险动作。
- 前端通过 SSE 接收 run 事件；停止、重新运行、导出仍通过 HTTP API 完成。

## 启动与安装排错

下面是本地启动时比较容易遇到的真实问题。

### 浏览器打开 `localhost:3000` 失败，或显示 `missing required error components`

现象：

```text
Port 3000 is in use, trying 3001 instead.
Local: http://localhost:3001
```

原因：

旧的 Next.js / Node 进程已经占用了 `3000` 端口，所以你新启动的前端自动跑到了 `3001`。如果这时还打开 `http://localhost:3000/runs/demo`，访问到的是旧进程，不是刚启动的新前端。

最快解决：

```text
http://localhost:3001/runs/demo
```

如果想继续使用 `3000`，先清理旧前端进程：

```powershell
Get-NetTCPConnection -LocalPort 3000,3001 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

cd "E:\codex\Navora Lite\navora-lite\apps\web"
pnpm.cmd dev
```

重新启动后再打开：

```text
http://localhost:3000/runs/demo
```

### `pnpm approve-builds` 在 PowerShell 中失败

现象：

```text
Ignored build scripts: unrs-resolver@...
Run "pnpm approve-builds" to pick which dependencies should be allowed to run scripts.
```

然后执行：

```powershell
pnpm approve-builds
```

出现：

```text
pnpm.ps1 cannot be loaded because running scripts is disabled on this system.
```

原因：

PowerShell 执行策略阻止了 `pnpm.ps1`。`Ignored build scripts` 这个 warning 通常不影响项目启动；如果你想按提示批准依赖构建脚本，需要使用 `.cmd` 启动器。

解决：

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\web"
pnpm.cmd approve-builds
```

在交互提示中选择 `unrs-resolver`，确认 approve，让 pnpm 执行 postinstall 脚本。后续前端命令也建议继续用：

```powershell
pnpm.cmd install
pnpm.cmd dev
pnpm.cmd build
```
