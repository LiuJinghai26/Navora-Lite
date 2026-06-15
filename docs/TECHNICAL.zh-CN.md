# Navora Lite 技术报告

本文档面向维护者和二次开发者，说明 Navora Lite 当前代码库的架构、模块职责、数据流、API、配置、执行边界和扩展位置。启动命令、依赖安装和常见排错以根目录 `README.md` 为准；本文重点解释实现细节。

## 1. 项目概览

Navora Lite 是一个本地优先的浏览器 Agent Dashboard。它把自然语言任务、浏览器动作执行、运行状态、截图记录和结构化结果放在一个轻量工作台中。

当前实现采用前后端分离：

- 前端：`apps/web`，Next.js 14、React、TypeScript、Zustand、Tailwind CSS。
- 后端：`apps/server`，FastAPI、Pydantic、HTTPX、Playwright。
- 存储：本地 JSON 文件，默认 `apps/server/data/runs.json`。
- 截图产物：默认 `apps/server/data/artifacts`，通过 `/artifacts/*` 暴露给前端。
- 实时通道：Server-Sent Events，端点为 `GET /api/runs/{run_id}/events`。
- 浏览器执行：使用 Playwright Chromium；当前代码没有 mock browser fallback。
- 规划器：先匹配内置 preset 和可识别任务，再调用 OpenAI-compatible Chat Completions 模型。

重要行为：

- Tasks 页面的 preset 任务不需要模型配置。
- New Chat 和 CLI 创建的自由任务需要先配置模型 API。
- 旧的本地 mock shopping flow 已被禁用，`/mock/findparts` 不再注册。
- 旧的 Aurora task lamp demo 不再是当前主流程。

## 2. 目录结构

```text
navora-lite/
  apps/
    server/
      app/
        agent/          动作模型、preset、浏览器会话、runner、安全检查
        api/            runs、events、settings、tasks 路由
        llm/            prompt、planner 调用、任务识别、planner 错误类型
        storage/        本地 runs store 与 SSE fan-out
        config.py       环境变量配置
        main.py         FastAPI 应用入口
        models.py       Pydantic API 与运行状态模型
      data/             本地运行记录和截图产物，开发运行时生成
      tests/            后端单元测试
      requirements.txt
    web/
      src/
        app/            Next.js App Router 页面
        components/     Sidebar、Chat、Preview、Timeline、Settings 等组件
        lib/            API client、SSE、Zustand store、主题、共享类型
      public/assets/    前端静态资源
      package.json
  docs/
    TECHNICAL.md        英文技术报告
    TECHNICAL.zh-CN.md  中文技术报告
  scripts/              run_demo、stop_run、export_run
  docker-compose.yml    可选后端容器启动方式
```

## 3. 后端架构

### 3.1 FastAPI 应用入口

`apps/server/app/main.py` 在 import 时完成应用装配：

- 从 `get_settings()` 读取缓存后的 `Settings`。
- 创建 `FastAPI(title="Navora Lite API", version="0.1.0")`。
- 配置 CORS，来源来自 `settings.cors_origin_list`。
- 确保 `settings.artifacts_dir` 存在。
- 把截图目录挂载到 `/artifacts`。
- 创建 `RunsStore(settings.run_storage_path)` 并保存到 `app.state.runs_store`。
- 注册 `runs`、`tasks`、`events`、`settings` 路由。
- 提供 `GET /health`。

当前 `main.py` 没有注册 mock commerce 页面，所以 `/mock/findparts` 返回 404。

### 3.2 配置模型

`apps/server/app/config.py` 使用 `pydantic-settings` 从当前工作目录下的 `.env` 读取配置。通常后端在 `apps/server` 目录启动，因此实际读取：

```text
apps/server/.env
```

核心配置项：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `MODEL_PROVIDER` | `openai-compatible` | 模型提供方标识。`ollama`、`lmstudio`、`vllm`、`custom` 被视为本地 provider，可不填 API key。 |
| `MODEL_NAME` | `qwen3-32b` | Chat Completions 请求里的模型名。 |
| `API_BASE` | 空 | OpenAI-compatible base URL，不含 `/chat/completions`。为空时自由任务不能 auto-start。 |
| `API_KEY` | 空 | Hosted-compatible provider 通常需要；本地 provider 可为空。 |
| `MAX_TOKENS` | `4096` | 模型输出 token 上限。 |
| `TEMPERATURE` | `0.2` | 模型温度。 |
| `LLM_TIMEOUT_SECONDS` | `60.0` | 模型请求超时时间。 |
| `BROWSER_HEADLESS` | `true` | Chromium 是否无头运行。`true` 不显示浏览器窗口；`false` 打开可见浏览器窗口。 |
| `BROWSER_CHANNEL` | `chromium` | 当前会写入 run inputs，但 Playwright launch 未使用 channel 参数。 |
| `BROWSER_VIEWPORT_WIDTH` | `1280` | 浏览器视口宽度。 |
| `BROWSER_VIEWPORT_HEIGHT` | `800` | 浏览器视口高度。 |
| `RUN_STORAGE_PATH` | `./data/runs.json` | run 本地持久化路径。 |
| `ARTIFACTS_DIR` | `./data/artifacts` | 截图产物目录。 |
| `RUNNER_STEP_DELAY_SECONDS` | `0.25` | 每个动作后的演示延迟。 |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | 允许跨域访问后端的前端来源。 |

`get_settings()` 使用 `lru_cache`，settings API 保存配置后会调用 `get_settings.cache_clear()`，让后续请求读取新的 `.env`。

### 3.3 数据模型

`apps/server/app/models.py` 定义后端与前端共享的核心结构，前端对应类型位于 `apps/web/src/lib/types.ts`。

主要模型：

- `Run`：一次浏览器任务的完整状态，包括任务、URL、状态、消息、时间线、截图、结构化提取结果、输入信息、失败类型和 stop 标记。
- `ChatMessage`：Chat Panel 中的用户、助手或系统消息，可包含 checklist。
- `ChecklistItem`：助手消息中的步骤清单。
- `TimelineStep`：单个浏览器动作的执行状态、耗时、错误和截图 URL。
- `ScreenshotItem`：Recording 与 Browser Preview 使用的截图元数据。
- `RunEvent`：SSE 推送事件。
- `SettingsPayload`：settings API 的读写结构。

`Run.status` 可取值：

```text
idle | running | completed | failed | stopped
```

`Run.controlStatus` 可取值：

```text
idle | controlling | stopped | completed | failed
```

`FailureType` 可取值：

```text
recognition_failed | planning_failed | execution_failed
```

## 4. Run 生命周期

### 4.1 创建 run

`POST /api/runs` 由 `apps/server/app/api/runs.py` 处理。

创建流程：

1. 读取当前 settings。
2. 通过 `_start_url_for_task()` 从 payload 或任务文本推断起始 URL。
3. 如果 `auto_start=true`、没有 `preset_id`、并且缺少 planner 配置，则返回 400。
4. 生成 `run_id`。
5. 创建 `Run`，初始状态为 `idle`，写入用户消息和 inputs。
6. 写入 `RunsStore`。
7. 如果 `auto_start=true`，把 `run_agent()` 加入 FastAPI `BackgroundTasks`。
8. 返回 `CreateRunResponse`。

自由任务需要模型配置的检查发生在 run 创建阶段。即使任务后续可能命中 `recognized_task_plan()`，如果没有模型配置也不会进入 runner。

### 4.2 执行 run

`apps/server/app/agent/runner.py` 的 `run_agent()` 是执行主循环。

执行流程：

1. 读取 run；不存在则直接返回。
2. 设置 `status=running` 和 `controlStatus=controlling`。
3. 调用 `plan_actions()` 获取动作列表。
4. 如果 planner 抛出识别、配置或模型错误，调用 `_mark_failed()`。
5. 如果 planner 返回 `fallback_reason`，当前 runner 也将其视为 planning failure。
6. 把动作列表转换为 checklist，并追加 assistant 消息。
7. 创建 Playwright browser session。
8. 对每个动作创建 running timeline step。
9. 调用 `assert_safe_action()` 做安全检查。
10. 执行浏览器动作。
11. 如果是 extract 动作，写入 `run.extracted` 并检查 blocked/empty 页面。
12. 截图并写入 artifacts。
13. 替换 timeline step 为 success，记录耗时和截图 URL。
14. 任一步失败则把 run 标记为 failed，并追加错误消息。
15. 全部动作成功后标记 run 为 completed，并追加完成消息。
16. 根据 `BROWSER_HEADLESS` 处理 browser session：headless 模式关闭浏览器；非 headless 模式断开 Playwright 控制连接但保留 Chromium 进程，便于任务结束后人工检查最终页面。

### 4.3 停止 run

`POST /api/runs/{run_id}/stop` 调用 `RunsStore.request_stop()`：

- 设置 `stopRequested=true`。
- 如果 run 正在运行，立即把状态置为 `stopped`。
- 发布 status 事件。

runner 在每个动作开始前检查 `stopRequested`。这意味着 stop 是动作边界生效，不会强行中断正在执行中的 Playwright 调用。

### 4.4 重新运行

`POST /api/runs/{run_id}/rerun` 会读取旧 run 的 `task`、`url` 和 `preset_id`，创建一个新的 run 并自动启动。旧 run 不会被覆盖。

## 5. Planner 与动作模型

### 5.1 动作模型

`apps/server/app/agent/actions.py` 定义 `AgentAction`：

```text
goto | click | fill | press | scroll | wait | extract | finish | ask_user
```

常用字段：

- `target`：语义目标，例如 `search input` 或 `hacker news top story`。
- `selector`：CSS selector，可绕过语义目标映射。
- `value`：fill 输入值。
- `url`：goto 目标 URL。
- `key`：press 按键。
- `direction`、`amount`：scroll 参数。
- `ms`、`condition`：wait 参数。
- `schema`：模型返回的提取结构；Python 字段为 `extract_schema`，通过 alias 暴露为 `schema`。

`describe_action()` 把动作转换为 timeline 文案。`target_to_selector()` 目前只包含少量搜索框/搜索按钮映射，更多真实站点定位依赖模型输出 selector 或 Playwright locator fallback。

### 5.2 Preset planner

`apps/server/app/agent/presets.py` 提供三个不依赖模型的 preset：

- `hn-top-story`
- `wikipedia-python-summary`
- `mdn-api-research`

这些 preset 由 Tasks 页启动，并通过 `preset_id` 传给后端。`preset_plan()` 会返回深拷贝动作，避免不同 run 共享同一个 Pydantic 对象。

### 5.3 识别型 planner

`recognized_task_plan()` 在调用模型前尝试识别一些常见任务和站点，例如：

- Ada Lovelace / Grace Hopper 的 Wikipedia 文章。
- Hacker News。
- GitHub Trending。
- MDN 文档页。
- timeanddate、weather、IKEA、Target、Nike、Best Buy、Amazon、Walmart、Booking、Tripadvisor、Expedia、Airbnb、Yelp、LinkedIn Jobs、Indeed、Remote OK、We Work Remotely、GitHub search、npm、PyPI、IANA、W3C WAI、httpbin test form。

识别型 planner 主要生成 `goto`、`wait`、`extract`，避免对复杂网站做脆弱的逐步点击。它不会绕过 `POST /api/runs` 的模型配置门槛；只有 preset 任务可以在没有模型配置时 auto-start。

### 5.4 模型 planner

当 preset 和识别型 planner 都没有命中时，`plan_actions()` 调用 OpenAI-compatible Chat Completions：

```text
POST {API_BASE}/chat/completions
```

请求包含：

- `model`
- `messages`
- `temperature`
- `max_tokens`

`SYSTEM_PROMPT` 要求模型只返回 JSON 动作数组，不包含 markdown 或解释文本。`_json_content()` 会容忍 fenced JSON 和额外文本，抽出最外层 JSON 数组或对象。`_parse_actions()` 支持模型把 `action` 写成 `type` 的兼容转换。

解析后会执行这些验证：

- 返回值必须是 list，或包含 `actions` 字段的对象。
- 至少要有一个可执行动作，`ask_user` 和 `finish` 不算可执行动作。
- 每个动作都会先经过 `assert_safe_action()`。

如果模型请求失败、返回异常结构或安全检查失败，`plan_actions()` 抛出 `PlannerError` 或相关子类，runner 会把 run 标为 failed。

## 6. 浏览器执行

`apps/server/app/agent/browser.py` 定义抽象 `BrowserSession` 和当前实现 `PlaywrightBrowserSession`。

### 6.1 Session 创建

`create_browser_session(settings)`：

1. 动态导入 `playwright.async_api.async_playwright`。
2. 启动 Playwright。
3. 如果 `BROWSER_HEADLESS=true`，使用 `playwright.chromium.launch(headless=True)` 无窗口执行。
4. 如果 `BROWSER_HEADLESS=false`，先启动独立 Chromium 进程，再通过 CDP 连接控制；任务结束后断开 Playwright，但不关闭该 Chromium 进程。
5. 创建指定 viewport 的 page。
6. 返回 `PlaywrightBrowserSession`。

如果导入、启动或 Chromium launch 失败，函数抛出 `RuntimeError`。runner 捕获后把 run 标为 `execution_failed`。

### 6.2 动作执行

`execute()` 根据 `action.type` 分发：

- `goto`：`page.goto(..., wait_until="domcontentloaded")`。
- `fill`：构造候选 selector 并调用 `_try_fill()`。
- `click`：先尝试 selector，再尝试按 role 查找 link/button。
- `press`：支持 `return`、`enter`、`esc` 别名。
- `scroll`：使用 mouse wheel。
- `wait`：等待指定毫秒。
- `extract`：先等待页面稳定，再按目标或 URL 调用提取器。

提取前 `_wait_for_page_settle()` 会尽量等待 `domcontentloaded`、`load` 和 `networkidle`。等待失败会被忽略，因为真实网站可能长时间保持连接。

### 6.3 提取器

内置提取器覆盖：

- Hacker News top story 和 stories。
- GitHub Trending repositories。
- Wikipedia Python summary 和通用 article summary。
- MDN Web API overview 和 Fetch API detail。
- httpbin form echo。
- 通用 page summary。

提取器通过 `page.evaluate()` 在页面内执行 JavaScript。`_evaluate()` 会在执行上下文销毁时重试三次，以应对导航或页面刷新。

### 6.4 截图

每个成功动作后都会截图：

```text
{run_id}_{action_index:02d}.png
```

截图写入 `ARTIFACTS_DIR`，前端通过 `/artifacts/{file_name}` 加载。

## 7. 安全边界

`apps/server/app/agent/safety.py` 使用关键词拦截高风险动作。

当前 `RISKY_TERMS` 包括：

- 支付、结账、提交订单、加入购物车。
- 删除账号、修改密码。
- captcha、2FA。
- 信用卡、密码、敏感信息。
- 上传私密文件。
- 部分中文风险词。

`DISALLOWED_MOCK_TERMS` 专门阻止旧 Aurora/mock shopping flow：

- `aurora task lamp`
- `mock/findparts`
- `localhost:8000/mock`
- `127.0.0.1:8000/mock`

这是本地 demo 级 guard，不等价于生产级权限系统、用户确认系统或完整风控。

## 8. 本地存储与事件

### 8.1 RunsStore

`apps/server/app/storage/runs_store.py` 是后端状态中心：

- 启动时从 JSON 文件加载历史 runs。
- 每次变更写回 JSON。
- 每个 run 可以有多个 SSE subscriber。
- 更新 run 时可以同步发布 `RunEvent`。

核心方法：

- `create_run`
- `get_run`
- `list_runs`
- `delete_run`
- `update_run`
- `add_message`
- `add_step`
- `replace_step`
- `add_screenshot`
- `set_status`
- `set_extracted`
- `request_stop`
- `publish`
- `subscribe`

当前存储适合单进程本地开发。它没有事务、锁、用户隔离或跨进程同步。

### 8.2 SSE

`GET /api/runs/{run_id}/events` 返回 `text/event-stream`。

连接建立后，服务端先发送：

```text
type=snapshot
```

snapshot 包含完整 `run`，用于初次加载和重连。后续事件包括：

| type | 说明 |
| --- | --- |
| `chat_message` | 追加聊天消息。 |
| `timeline_step` | 新增或替换 timeline step。 |
| `screenshot` | 新截图可用。 |
| `status` | run 状态变化。 |
| `extracted` | 结构化提取结果更新。 |

多数事件带完整 `run` 字段。前端 store 会优先采用 `event.run`，减少局部合并产生的不一致。

## 9. API 参考

### 9.1 健康检查

```http
GET /health
```

响应：

```json
{"status":"ok","app":"navora-lite"}
```

### 9.2 创建 run

```http
POST /api/runs
Content-Type: application/json
```

请求：

```json
{
  "task": "Open Hacker News and extract the current top story.",
  "url": "https://news.ycombinator.com/",
  "auto_start": true,
  "preset_id": "hn-top-story"
}
```

响应：

```json
{
  "run_id": "run_xxxxxxxxxxxxxxxxxx",
  "status": "running"
}
```

说明：

- `auto_start=false` 时只创建 idle run。
- `preset_id` 可为空。
- `auto_start=true` 且没有 `preset_id` 时，需要模型配置。

### 9.3 列出 runs

```http
GET /api/runs
```

响应是 `Run[]`，按 `startedAt` 倒序排序。

### 9.4 获取 run

```http
GET /api/runs/{run_id}
```

响应是完整 `Run`。不存在返回 404。

### 9.5 停止 run

```http
POST /api/runs/{run_id}/stop
```

响应是更新后的 `Run`。不存在返回 404。

### 9.6 重新运行

```http
POST /api/runs/{run_id}/rerun
```

响应是新的 `CreateRunResponse`。后端会复制旧 run 的任务、URL 和 preset 元数据。

### 9.7 SSE 事件

```http
GET /api/runs/{run_id}/events
```

服务端返回 `text/event-stream`，每条消息格式：

```text
data: {...}
```

### 9.8 任务历史

```http
GET /api/tasks
DELETE /api/tasks/{run_id}
```

`GET /api/tasks` 返回 run history，当前与 `GET /api/runs` 使用同一个存储。`DELETE` 删除本地历史记录和订阅者集合。

### 9.9 设置

```http
GET /api/settings
POST /api/settings
```

`GET` 返回当前 settings，其中非空 `API_KEY` 会被掩码为 `********`。

`POST` 会：

1. 序列化 payload。
2. 写入当前工作目录下的 `.env`。
3. 保留未涉及的 `.env` 行。
4. 如果 `API_KEY` 是 `********`，不覆盖已有 key。
5. 清除 `get_settings()` 缓存。
6. 返回最新 settings。

## 10. 前端架构

### 10.1 页面

`apps/web/src/app` 使用 Next.js App Router：

- `/`：重定向到 `/new-chat`。
- `/new-chat`：自由任务输入页，会先检查模型配置。
- `/runs/[runId]`：运行详情页，加载 run 并订阅 SSE。
- `/tasks`：任务历史与 preset demo。
- `/sessions`：当前浏览器会话概览。
- `/settings`：主题与模型设置。
- `/agents`：重定向到 `/tasks`。

### 10.2 API client

`apps/web/src/lib/api.ts` 使用：

```text
NEXT_PUBLIC_API_BASE || http://localhost:8000
```

主要函数：

- `getRun`
- `getTasks`
- `deleteTask`
- `createRun`
- `stopRun`
- `rerun`
- `getSettings`
- `saveSettings`

`request()` 会优先读取后端 JSON 中的 `detail` 作为错误消息。204 响应返回 `undefined`。

### 10.3 SSE client

`apps/web/src/lib/events.ts` 使用浏览器原生 `EventSource`。SSE 只负责后端到前端的状态推送；停止、重新运行、删除等控制动作仍通过 HTTP API。

### 10.4 状态管理

`apps/web/src/lib/store.ts` 使用 Zustand 管理：

- `run`：当前 run，初始值是 bundled `sampleRun`。
- `activeTab`：当前 RunTabs。
- `apiOnline`：后端连接状态。
- `applyEvent(event)`：合并 SSE 事件。

如果 event 带完整 `run`，store 直接覆盖本地 run。否则按事件类型局部更新消息、时间线、状态和提取结果。

### 10.5 UI 组件

核心组件位于 `apps/web/src/components`：

- `app-sidebar.tsx`：导航、任务统计、失败类型统计。
- `chat-panel.tsx`、`chat-message.tsx`：任务对话与 checklist。
- `browser-preview.tsx`、`fullscreen-preview-dialog.tsx`：截图预览与全屏。
- `execution-timeline.tsx`：步骤时间线和截图选择。
- `extracted-information.tsx`：结构化 JSON 结果展示与复制。
- `run-header.tsx`：run 元信息、导出、rerun、API 示例弹窗。
- `run-tabs.tsx`：Overview、Output、Inputs、Recording、Code tabs。
- `model-settings-dialog.tsx`：模型配置弹窗。
- `status-badge.tsx`：状态视觉映射。
- `theme-provider.tsx`：主题初始化和跨组件同步。

### 10.6 主题

主题由 CSS 变量和 `data-theme` 控制：

- `deep-blue`
- `light`
- `warm`

`theme.ts` 使用 `localStorage` 持久化主题，并通过 `navora-theme-change` 自定义事件通知已挂载组件。

## 11. 开发与验证

### 11.1 后端测试

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\server"
.\.venv\Scripts\python.exe -m pytest
```

不使用虚拟环境：

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\server"
python -m pytest
```

当前测试覆盖：

- planner JSON 解析、fenced JSON、`action` alias。
- 禁用旧 mock flow。
- 常见任务识别。
- blocked/empty 提取结果判定。
- preset planner 输出。
- runner 对 planner fallback 的失败标记。
- runs API 创建、读取、停止、rerun 相关行为。
- tasks API 列表和删除。
- safety guard。

### 11.2 前端构建

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\web"
pnpm.cmd build
```

### 11.3 CLI 验证

CLI 创建自由任务，需要先配置模型：

```powershell
cd "E:\codex\Navora Lite\navora-lite"
python scripts/run_demo.py `
  --task "Open Hacker News and extract the current top story with its source, score, age, and comments." `
  --url "https://news.ycombinator.com/"
```

无模型配置时，请从前端 Tasks 页启动 preset 任务。

## 12. 扩展指南

### 12.1 增加新动作

需要同步修改：

1. `apps/server/app/agent/actions.py`：扩展 `AgentAction.type` 和描述逻辑。
2. `apps/server/app/agent/browser.py`：在 `PlaywrightBrowserSession.execute()` 中实现动作。
3. `apps/server/app/agent/safety.py`：评估动作是否需要额外拦截。
4. `apps/server/app/llm/prompts.py`：让模型知道新动作的输出格式。
5. `apps/web/src/lib/types.ts`：如果 timeline 或事件结构变化，更新前端类型。
6. `apps/server/tests`：补充 planner、runner 或 safety 测试。

### 12.2 增加 preset

需要同步修改：

1. `apps/server/app/agent/presets.py`：新增 `PRESET_TASKS` 条目。
2. `apps/web/src/lib/preset-tasks.ts`：新增前端 preset 卡片。
3. `apps/web/src/app/tasks/page.tsx`：如需图标，扩展 `presetIcons`。
4. `apps/server/tests/test_planner.py`：验证 preset 动作序列。

### 12.3 接入真实站点

建议路径：

- 优先让 planner 输出稳定 selector。
- 对搜索、导航、提取这类动作保持粗粒度，减少脆弱点击。
- 为每个目标站点添加独立提取器，而不是把所有提取都交给通用 page summary。
- 对登录、支付、提交、上传等动作增加显式用户确认，不要直接放宽关键词 guard。

### 12.4 替换存储

如果把 `RunsStore` 替换为数据库，需要保留：

- run CRUD。
- timeline/message/screenshot/extracted 的原子更新语义。
- status 与 controlStatus 的联动。
- SSE 事件发布。
- 删除历史时清理订阅者或外部消息通道。

多进程或多实例部署时，SSE 不能依赖进程内 queue，需要迁移到 Redis Pub/Sub、数据库通知或消息队列。

## 13. 当前限制

- 本地 JSON 存储不适合多用户、多实例或高并发。
- 没有鉴权、用户隔离和权限模型。
- 停止 run 只在动作边界生效。
- `BROWSER_CHANNEL` 没有传给 Playwright launch channel。
- Playwright 启动失败时没有 mock browser fallback。
- 自由任务即使可被 `recognized_task_plan()` 识别，也仍需先通过模型配置门槛。
- 安全检查是关键词级 guard，不是生产级风控。
- settings API 写入当前工作目录的 `.env`，部署时需要保证工作目录正确。
- 前端 `sampleRun` 只用于无后端时的初始展示，不代表实时数据。
