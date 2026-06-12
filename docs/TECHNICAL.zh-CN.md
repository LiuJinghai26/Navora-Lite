# Navora Lite 技术文档

本文档面向维护者和二次开发者，说明 Navora Lite 的运行架构、主要模块、数据流、API、配置项和扩展位置。启动命令和常见问题以根目录 `README.zh-CN.md` 为准，本文重点补充实现层面的细节。

## 1. 系统概览

Navora Lite 是一个本地优先的浏览器 Agent Dashboard，采用前后端分离结构：

- 前端：`apps/web`，Next.js 14、React、TypeScript、Zustand、Tailwind CSS。
- 后端：`apps/server`，FastAPI、Pydantic、HTTPX、Playwright。
- 存储：本地 JSON 文件 `apps/server/data/runs.json`。
- 实时通道：Server-Sent Events，端点为 `GET /api/runs/{run_id}/events`。
- 浏览器执行：优先使用 Playwright Chromium；不可用时回退到 `MockBrowserSession`。
- 规划器：优先调用 OpenAI-compatible Chat Completions 接口；缺少配置或模型异常时回退到 mock planner。

默认 demo 可以在没有真实模型服务和没有可用 Chromium 的情况下跑通。模型 fallback 负责产生固定动作计划，浏览器 fallback 负责生成可检查的 SVG 截图。

## 2. 目录结构

```text
navora-lite/
  apps/
    server/
      app/
        agent/          浏览器动作、执行器、安全检查和 browser session
        api/            runs、events、settings API
        llm/            planner prompt、模型调用和 mock plan
        storage/        本地 runs store
        config.py       后端环境变量配置
        main.py         FastAPI 应用入口
        models.py       Pydantic API/状态模型
      data/             本地运行记录和截图产物，开发生成
      tests/            后端单元测试
      requirements.txt
    web/
      src/
        app/            Next.js App Router 页面
        components/     Dashboard、Chat、Preview、Timeline 等 UI 组件
        lib/            API、SSE、状态 store、共享类型
      public/assets/
      package.json
  docs/
    TECHNICAL.zh-CN.md
  scripts/              run_demo、stop_run、export_run
  docker-compose.yml    可选后端容器启动方式
```

## 3. 后端模块

### 3.1 FastAPI 入口

`apps/server/app/main.py` 创建 FastAPI app，并完成这些初始化：

- 加载 `Settings`。
- 配置 CORS。
- 确保 `ARTIFACTS_DIR` 存在。
- 将 `ARTIFACTS_DIR` 挂载到 `/artifacts`。
- 创建 `RunsStore` 并挂到 `app.state.runs_store`。
- 注册 `runs`、`events`、`settings` 路由。
- 提供 `/health` 和 `/mock/findparts`。

### 3.2 配置模型

`apps/server/app/config.py` 使用 `pydantic-settings` 从当前工作目录下的 `.env` 读取配置。通常后端应在 `apps/server` 目录启动，因此实际读取的是：

```text
apps/server/.env
```

核心配置项：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `MODEL_PROVIDER` | `openai-compatible` | 模型提供方标识。`ollama`、`lmstudio`、`vllm`、`custom` 允许空 API key。 |
| `MODEL_NAME` | `qwen3-32b` | Chat Completions 请求中的模型名。 |
| `API_BASE` | 空 | 模型服务 base URL，不含 `/chat/completions`。为空时使用 mock planner。 |
| `API_KEY` | 空 | Hosted-compatible 服务通常需要；本地 provider 可为空。 |
| `MAX_TOKENS` | `4096` | 模型输出 token 上限。 |
| `TEMPERATURE` | `0.2` | 模型温度。 |
| `LLM_TIMEOUT_SECONDS` | `20.0` | 模型请求超时时间。 |
| `BROWSER_HEADLESS` | `true` | Chromium 是否无头运行。 |
| `BROWSER_CHANNEL` | `chromium` | 当前配置字段存在，但执行器实际使用 `playwright.chromium`。 |
| `BROWSER_VIEWPORT_WIDTH` | `1280` | 浏览器视口宽度。 |
| `BROWSER_VIEWPORT_HEIGHT` | `800` | 浏览器视口高度。 |
| `RUN_STORAGE_PATH` | `./data/runs.json` | run 本地持久化路径。 |
| `ARTIFACTS_DIR` | `./data/artifacts` | 截图和 mock SVG 产物目录。 |
| `RUNNER_STEP_DELAY_SECONDS` | `0.25` | 每个动作之间的演示延迟。 |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | 前端允许跨域来源。 |

### 3.3 数据模型

`apps/server/app/models.py` 定义后端返回给前端的主要结构。前端在 `apps/web/src/lib/types.ts` 中维护对应 TypeScript 类型。

核心对象：

- `Run`：一次浏览器任务的完整状态，包括任务、URL、状态、消息、timeline、截图、提取结果和输入信息。
- `ChatMessage`：Chat Panel 中的用户、助手或系统消息。
- `TimelineStep`：单个浏览器动作的执行状态。
- `ScreenshotItem`：Recording 和 Browser Preview 使用的截图元数据。
- `RunEvent`：SSE 推送事件。

`Run.status` 可取值：

```text
idle | running | completed | failed | stopped
```

`Run.controlStatus` 可取值：

```text
idle | controlling | stopped | completed | failed
```

### 3.4 本地存储

`apps/server/app/storage/runs_store.py` 提供内存 + JSON 文件的轻量存储：

- 启动时从 `RUN_STORAGE_PATH` 加载历史 runs。
- 每次 `create_run`、`update_run`、`add_step`、`add_message`、`set_status` 等变更都会写回 JSON。
- 每个 run 可以有多个 SSE subscriber。
- `update_run(..., event=...)` 会在持久化后向当前订阅者发布事件。

当前实现适合本地 demo 和单进程开发。它没有数据库事务、跨进程同步或用户隔离能力；如果部署为多实例服务，需要替换为数据库和消息通道。

## 4. Run 生命周期

一次默认任务的流程如下：

1. 前端调用 `POST /api/runs`，提交 `task` 和 `url`。
2. 后端创建 `Run`，初始写入用户消息和 `inputs`。
3. 如果 `auto_start=true`，FastAPI `BackgroundTasks` 在响应后调用 `run_agent`。
4. 前端跳转或订阅 `GET /api/runs/{run_id}/events`。
5. SSE 首包发送 `snapshot`，其中包含当前完整 `Run`。
6. `run_agent` 将 run 置为 `running` 和 `controlling`。
7. `plan_actions` 调用模型 planner；如果失败或未配置模型，则返回 mock plan 和 `fallback_reason`。
8. runner 为 planner 动作生成 assistant checklist。
9. runner 创建 browser session，优先 Playwright，失败则 mock browser。
10. 每个动作执行前发布 `running` timeline step。
11. 动作执行成功后写截图、更新 step 为 `success`，必要时写入 `extracted`。
12. 任一步失败时，step 标记为 `failed`，run 标记为 `failed`，并追加 assistant 错误消息。
13. 全部动作成功后，run 标记为 `completed`，追加完成消息。

停止流程：

- `POST /api/runs/{run_id}/stop` 会设置 `stopRequested=true`。
- 如果 run 正在运行，会立即把状态置为 `stopped`。
- runner 在动作边界检查 `stopRequested`，随后追加 stop step 和停止消息。

## 5. Agent 规划与执行

### 5.1 动作模型

`apps/server/app/agent/actions.py` 中的 `AgentAction` 支持这些动作类型：

```text
goto | click | fill | press | scroll | wait | extract | finish | ask_user
```

常用字段：

- `target`：语义目标，例如 `search input`、`quantity`、`cart`。
- `selector`：CSS selector，可绕过 `target_to_selector` 映射。
- `value`：fill 动作输入值。
- `url`：goto 动作目标 URL。
- `key`：press 动作按键。
- `schema`：extract 动作期望提取结构，对应 Python 字段 `extract_schema`。

### 5.2 Mock planner

`apps/server/app/llm/client.py` 的 `mock_plan` 返回固定 demo 路径：

1. 打开 mock FindItParts 页面。
2. 搜索 `FIRESTONE W01-377-8537`。
3. 点击搜索按钮。
4. 打开商品。
5. 设置数量为 `1`。
6. 加入购物车。
7. 打开购物车。
8. 提取 `{ product_name, quantity }`。

当 `API_BASE` 为空、缺少必要 API key、模型超时、模型返回非法 JSON 或高风险动作时，后端使用 mock planner。

### 5.3 模型 planner

模型 planner 调用 OpenAI-compatible Chat Completions：

```text
POST {API_BASE}/chat/completions
```

请求包含：

- `model`
- `messages`
- `temperature`
- `max_tokens`

模型必须只返回 JSON。可以返回动作数组，也可以返回包含 `actions` 字段的对象。返回内容会被解析为 `AgentAction` 列表，并在执行前进行安全检查。

### 5.4 浏览器 session

`apps/server/app/agent/browser.py` 有两种实现：

- `PlaywrightBrowserSession`：使用 Chromium 真实执行页面动作并截图。
- `MockBrowserSession`：在没有 Playwright 或 Chromium 不可用时模拟状态变化，并生成 SVG 截图。

Playwright 的 `extract` 针对 mock 页面读取稳定属性：

- `data-product-name`
- `data-cart-quantity`
- `#cart-product-name`
- `#cart-quantity`
- `#quantity`

这使 demo 的提取结果在测试和本地演示中保持稳定。

### 5.5 安全边界

`apps/server/app/agent/safety.py` 对动作文本进行关键词检查，命中后抛出：

```text
This step requires user confirmation.
```

当前拦截范围包括：

- 支付、结账、提交订单。
- 删除账号、修改密码。
- 验证码、2FA。
- 信用卡、密码等敏感信息。
- 上传私密文件。
- 对应的部分中文关键词。

这是一个保守的本地 demo guard，不等价于生产级风控或权限系统。

## 6. API 参考

### 6.1 健康检查

```http
GET /health
```

响应：

```json
{"status":"ok","app":"navora-lite"}
```

### 6.2 创建 run

```http
POST /api/runs
Content-Type: application/json
```

请求：

```json
{
  "task": "Add FIRESTONE W01-377-8537 to the cart and set quantity to 1",
  "url": "http://localhost:8000/mock/findparts",
  "auto_start": true
}
```

响应：

```json
{
  "run_id": "run_xxxxxxxxxxxxxxxxxx",
  "status": "running"
}
```

说明：当 `auto_start=false` 时，响应状态为 `idle`；当前 API 没有单独的 start endpoint。

### 6.3 列出 runs

```http
GET /api/runs
```

响应是 `Run[]`，按 `startedAt` 倒序返回。没有 `startedAt` 的 run 会排在较后位置。

### 6.4 获取 run

```http
GET /api/runs/{run_id}
```

响应是完整 `Run`。

### 6.5 停止 run

```http
POST /api/runs/{run_id}/stop
```

响应是更新后的 `Run`。如果 run 不存在，返回 `404`。

### 6.6 重新运行

```http
POST /api/runs/{run_id}/rerun
```

后端读取旧 run 的 `task` 和 `url`，创建一个新的 run 并自动启动。响应是新的 `run_id`。

### 6.7 SSE 事件

```http
GET /api/runs/{run_id}/events
```

服务端返回 `text/event-stream`。每条消息格式：

```text
data: {...}
```

事件类型：

| type | 说明 |
| --- | --- |
| `snapshot` | 首包完整 run，用于初次加载或重连。 |
| `chat_message` | 追加聊天消息。 |
| `timeline_step` | 新增或替换 timeline step。 |
| `screenshot` | 新截图可用。 |
| `status` | run 状态变化。 |
| `extracted` | 结构化提取结果更新。 |

多数事件会带 `run` 字段。前端 store 会优先信任 `event.run`，这样重连和局部更新逻辑更简单。

### 6.8 设置

```http
GET /api/settings
POST /api/settings
```

`GET` 返回当前后端配置，其中 `API_KEY` 会被掩码为 `********`。`POST` 当前只回显请求体，不会写入 `.env`，也不会刷新后端运行中的 `Settings` 缓存。设置页因此更接近 UI 原型，不是持久配置管理。

### 6.9 Mock 页面和静态产物

```http
GET /mock/findparts
GET /artifacts/{file_name}
```

`/mock/findparts` 返回内置 HTML demo 页面。`/artifacts/*` 由 FastAPI 静态文件服务暴露，用于前端展示截图。

## 7. 前端模块

### 7.1 页面

`apps/web/src/app` 使用 Next.js App Router：

- `/`：入口页。
- `/runs/[runId]`：主要运行详情页。
- `/agents`、`/sessions`、`/settings`：Dashboard 侧边栏相关页面。

### 7.2 API 和 SSE

`apps/web/src/lib/api.ts` 使用 `NEXT_PUBLIC_API_BASE` 拼接后端 URL，默认：

```text
http://localhost:8000
```

主要函数：

- `getRun(runId)`
- `createRun(task, url)`
- `stopRun(runId)`
- `rerun(runId)`
- `getSettings()`
- `saveSettings(payload)`

`apps/web/src/lib/events.ts` 使用浏览器原生 `EventSource` 订阅 run 事件。

### 7.3 状态管理

`apps/web/src/lib/store.ts` 使用 Zustand 管理当前 run：

- `run`：当前展示的 run。
- `activeTab`：Overview、Output、Inputs、Recording、Code 等 tab。
- `apiOnline`：后端连接状态。
- `applyEvent(event)`：把 SSE 事件合并到前端状态。

如果 SSE 事件包含完整 `run`，store 直接用它覆盖本地 run；否则按事件类型局部更新。

### 7.4 UI 组件

主要组件位于 `apps/web/src/components`：

- `app-sidebar.tsx`：侧边导航。
- `chat-panel.tsx`、`chat-message.tsx`：任务输入和消息展示。
- `browser-preview.tsx`、`fullscreen-preview-dialog.tsx`：截图预览。
- `execution-timeline.tsx`：动作时间线。
- `extracted-information.tsx`：结构化提取结果。
- `run-header.tsx`、`run-tabs.tsx`、`status-badge.tsx`：run 元信息和导航。
- `model-settings-dialog.tsx`：模型设置 UI。

## 8. 开发与验证

### 8.1 后端测试

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\server"
.\.venv\Scripts\python.exe -m pytest
```

不使用虚拟环境时：

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\server"
python -m pytest
```

当前测试覆盖：

- planner fallback 和动作规划。
- runs API 创建、查询等行为。
- safety guard。

### 8.2 前端构建

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\web"
pnpm.cmd build
```

### 8.3 CLI 验证

后端启动后：

```powershell
cd "E:\codex\Navora Lite\navora-lite"
python scripts/run_demo.py `
  --task "Add FIRESTONE W01-377-8537 to the cart and set quantity to 1" `
  --url "http://localhost:8000/mock/findparts"
```

成功时应看到：

```json
{
  "status": "completed",
  "extracted": {
    "product_name": "FIRESTONE W01-377-8537",
    "quantity": 1
  }
}
```

## 9. 扩展指南

### 9.1 增加新动作

需要同步修改：

1. `apps/server/app/agent/actions.py`：扩展 `AgentAction.type`、描述逻辑和必要字段。
2. `apps/server/app/agent/browser.py`：在 `PlaywrightBrowserSession.execute` 中实现动作。
3. `apps/server/app/agent/safety.py`：评估动作是否需要额外拦截。
4. `apps/web/src/lib/types.ts`：如果 timeline 或事件结构变化，更新前端类型。
5. `apps/server/tests`：补充 planner、runner 或 safety 测试。

### 9.2 接入真实站点

最小修改路径：

- 在 `createRun` 时传入真实 `url`。
- 为模型 planner 提供能定位页面元素的 prompt。
- 尽量让 planner 输出稳定 `selector`，减少依赖 `target_to_selector` 的 mock 映射。
- 为高风险操作加入显式确认流程，而不是直接放宽 `safety.py`。

### 9.3 替换存储

`RunsStore` 是后端状态中心。替换为数据库时，需要保留这些语义：

- `create_run`
- `get_run`
- `list_runs`
- `update_run`
- `add_message`
- `add_step`
- `replace_step`
- `add_screenshot`
- `set_status`
- `set_extracted`
- `request_stop`
- `subscribe` / `publish`

如果使用多进程或多实例部署，SSE 事件需要从进程内 queue 迁移到 Redis Pub/Sub、数据库通知或消息队列。

## 10. 当前限制

- settings API 不持久化配置。
- 本地 JSON 存储不适合多用户或多实例部署。
- 停止 run 是动作边界生效，不会强行中断正在执行的 Playwright 操作。
- `BROWSER_CHANNEL` 配置当前没有传给 Playwright launch channel。
- mock planner 是固定 FIRESTONE demo 路径，不具备通用站点规划能力。
- 安全检查是关键词级 guard，不是完整权限系统。
