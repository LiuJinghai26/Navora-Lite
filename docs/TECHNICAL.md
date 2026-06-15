# Navora Lite Technical Report

This document is for maintainers and secondary developers. It explains the current Navora Lite architecture, module responsibilities, data flow, APIs, configuration, execution boundaries, and extension points. Use the root `README.md` for setup commands, dependency installation, and common troubleshooting; this report focuses on implementation details.

## 1. Project Overview

Navora Lite is a local-first browser Agent Dashboard. It combines natural-language task entry, browser action execution, run state, screenshots, and structured extraction output in one lightweight workspace.

The current implementation is split into frontend and backend apps:

- Frontend: `apps/web`, built with Next.js 14, React, TypeScript, Zustand, and Tailwind CSS.
- Backend: `apps/server`, built with FastAPI, Pydantic, HTTPX, and Playwright.
- Storage: local JSON file, defaulting to `apps/server/data/runs.json`.
- Artifacts: screenshots under `apps/server/data/artifacts`, exposed through `/artifacts/*`.
- Realtime channel: Server-Sent Events at `GET /api/runs/{run_id}/events`.
- Browser execution: Playwright Chromium. The current code does not include a mock browser fallback.
- Planning: built-in presets and recognized task plans first, then an OpenAI-compatible Chat Completions model.

Important current behavior:

- Preset tasks from the Tasks page do not require model configuration.
- Free-form tasks from New Chat or the CLI require model API settings before auto-start.
- The old local mock shopping flow is disabled, and `/mock/findparts` is not registered.
- The old Aurora task lamp demo is no longer the main workflow.

## 2. Directory Structure

```text
navora-lite/
  apps/
    server/
      app/
        agent/          Action model, presets, browser session, runner, safety checks
        api/            Runs, events, settings, and tasks routes
        llm/            Prompt, planner call, task recognition, planner error types
        storage/        Local runs store and SSE fan-out
        config.py       Environment-driven backend settings
        main.py         FastAPI application entry point
        models.py       Pydantic API and run-state models
      data/             Generated local run records and screenshots
      tests/            Backend tests
      requirements.txt
    web/
      src/
        app/            Next.js App Router pages
        components/     Sidebar, chat, preview, timeline, settings, and run UI
        lib/            API client, SSE, Zustand store, themes, shared types
      public/assets/    Frontend static assets
      package.json
  docs/
    TECHNICAL.md        English technical report
    TECHNICAL.zh-CN.md  Chinese technical report
  scripts/              run_demo, stop_run, export_run
  docker-compose.yml    Optional backend-only container workflow
```

## 3. Backend Architecture

### 3.1 FastAPI Application Entry

`apps/server/app/main.py` assembles the backend application at import time:

- Reads cached `Settings` through `get_settings()`.
- Creates `FastAPI(title="Navora Lite API", version="0.1.0")`.
- Configures CORS from `settings.cors_origin_list`.
- Ensures `settings.artifacts_dir` exists.
- Mounts the screenshot directory at `/artifacts`.
- Creates `RunsStore(settings.run_storage_path)` and stores it on `app.state.runs_store`.
- Registers the `runs`, `tasks`, `events`, and `settings` routers.
- Exposes `GET /health`.

`main.py` does not register a mock commerce page, so `/mock/findparts` returns 404.

### 3.2 Settings Model

`apps/server/app/config.py` uses `pydantic-settings` to read `.env` from the current working directory. In normal local development, the backend starts from `apps/server`, so the effective file is:

```text
apps/server/.env
```

Core settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MODEL_PROVIDER` | `openai-compatible` | Provider label. `ollama`, `lmstudio`, `vllm`, and `custom` are local providers and may omit API keys. |
| `MODEL_NAME` | `qwen3-32b` | Model name sent to Chat Completions. |
| `API_BASE` | empty | OpenAI-compatible base URL without `/chat/completions`. Free-form runs cannot auto-start when empty. |
| `API_KEY` | empty | Usually required for hosted-compatible providers; optional for local providers. |
| `MAX_TOKENS` | `4096` | Planner response token limit. |
| `TEMPERATURE` | `0.2` | Planner sampling temperature. |
| `LLM_TIMEOUT_SECONDS` | `60.0` | HTTP timeout for planner calls. |
| `BROWSER_HEADLESS` | `true` | Whether Chromium runs headlessly. `true` shows no browser window; `false` opens a visible browser window. |
| `BROWSER_CHANNEL` | `chromium` | Stored in run inputs, but not passed as a Playwright launch channel. |
| `BROWSER_VIEWPORT_WIDTH` | `1280` | Browser viewport width. |
| `BROWSER_VIEWPORT_HEIGHT` | `800` | Browser viewport height. |
| `RUN_STORAGE_PATH` | `./data/runs.json` | Local run persistence path. |
| `ARTIFACTS_DIR` | `./data/artifacts` | Screenshot artifact directory. |
| `RUNNER_STEP_DELAY_SECONDS` | `0.25` | Demo delay after each action. |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed frontend origins. |

`get_settings()` is cached with `lru_cache`. The settings API clears that cache after writing `.env`, so later requests read the updated file.

### 3.3 Data Models

`apps/server/app/models.py` defines the backend models shared with the frontend. The matching TypeScript types live in `apps/web/src/lib/types.ts`.

Primary models:

- `Run`: complete state for one browser task, including task, URL, status, messages, timeline, screenshots, extraction output, inputs, failure type, and stop flag.
- `ChatMessage`: user, assistant, or system messages shown in the Chat Panel.
- `ChecklistItem`: assistant checklist items.
- `TimelineStep`: browser action status, timing, error, and screenshot URL.
- `ScreenshotItem`: screenshot metadata for Recording and Browser Preview.
- `RunEvent`: SSE payload model.
- `SettingsPayload`: settings API read/write shape.

`Run.status` values:

```text
idle | running | completed | failed | stopped
```

`Run.controlStatus` values:

```text
idle | controlling | stopped | completed | failed
```

`FailureType` values:

```text
recognition_failed | planning_failed | execution_failed
```

## 4. Run Lifecycle

### 4.1 Run Creation

`POST /api/runs` is handled by `apps/server/app/api/runs.py`.

Creation flow:

1. Read current settings.
2. Infer the start URL from the payload or task text through `_start_url_for_task()`.
3. If `auto_start=true`, no `preset_id` is present, and planner settings are missing, return 400.
4. Generate a `run_id`.
5. Create a `Run` with initial `idle` state, user message, and inputs.
6. Persist it through `RunsStore`.
7. If `auto_start=true`, schedule `run_agent()` with FastAPI `BackgroundTasks`.
8. Return `CreateRunResponse`.

The model-configuration gate happens before the runner starts. Even if a task could later match `recognized_task_plan()`, a free-form auto-start run still needs model configuration. Presets are the model-free path.

### 4.2 Run Execution

`apps/server/app/agent/runner.py` contains the execution loop in `run_agent()`.

Execution flow:

1. Load the run; return if missing.
2. Set `status=running` and `controlStatus=controlling`.
3. Call `plan_actions()` for actions.
4. Mark the run failed if planning raises recognition, configuration, or model errors.
5. Treat a planner `fallback_reason` as a planning failure.
6. Convert actions to a checklist and append an assistant message.
7. Create a Playwright browser session.
8. Create a running timeline step for each action.
9. Run `assert_safe_action()` before browser side effects.
10. Execute the browser action.
11. For extract actions, write `run.extracted` and check blocked or empty pages.
12. Save a screenshot under artifacts.
13. Replace the timeline step with final success state, duration, and screenshot URL.
14. On any action failure, mark the run failed and append an assistant error message.
15. After all actions succeed, mark the run completed and append a completion message.
16. Handle the browser session according to `BROWSER_HEADLESS`: headless runs close the browser, while visible runs detach Playwright control and keep the Chromium process open for post-run inspection.

### 4.3 Stop Flow

`POST /api/runs/{run_id}/stop` calls `RunsStore.request_stop()`:

- Sets `stopRequested=true`.
- If the run is currently running, sets `status=stopped` and `controlStatus=stopped`.
- Publishes a status event.

The runner checks `stopRequested` before starting each action. Stopping therefore takes effect at action boundaries and does not forcibly interrupt an in-flight Playwright call.

### 4.4 Rerun Flow

`POST /api/runs/{run_id}/rerun` reads the old run's `task`, `url`, and `preset_id`, then creates and auto-starts a new run. The original run remains unchanged.

## 5. Planner and Action Model

### 5.1 Action Model

`apps/server/app/agent/actions.py` defines `AgentAction`:

```text
goto | click | fill | press | scroll | wait | extract | finish | ask_user
```

Common fields:

- `target`: semantic target such as `search input` or `hacker news top story`.
- `selector`: CSS selector that bypasses semantic target mapping.
- `value`: input value for fill actions.
- `url`: navigation URL for goto actions.
- `key`: key name for press actions.
- `direction`, `amount`: scroll parameters.
- `ms`, `condition`: wait parameters.
- `schema`: planner-provided extraction schema; the Python field is `extract_schema` with a `schema` alias.

`describe_action()` converts actions into timeline text. `target_to_selector()` currently maps only a few search targets; most real-site positioning depends on selectors from the model or Playwright locator fallbacks.

### 5.2 Preset Planner

`apps/server/app/agent/presets.py` defines three model-free presets:

- `hn-top-story`
- `wikipedia-python-summary`
- `mdn-api-research`

The Tasks page starts these presets by sending `preset_id` to the backend. `preset_plan()` returns deep copies of preset actions so runs do not share mutable Pydantic objects.

### 5.3 Recognized Task Planner

`recognized_task_plan()` tries known task and site patterns before calling a model, including:

- Ada Lovelace and Grace Hopper Wikipedia articles.
- Hacker News.
- GitHub Trending.
- MDN documentation pages.
- timeanddate, weather, IKEA, Target, Nike, Best Buy, Amazon, Walmart, Booking, Tripadvisor, Expedia, Airbnb, Yelp, LinkedIn Jobs, Indeed, Remote OK, We Work Remotely, GitHub search, npm, PyPI, IANA, W3C WAI, and httpbin test forms.

Recognized plans are usually coarse `goto`, `wait`, and `extract` sequences. They avoid brittle clicking where direct URLs are more reliable.

### 5.4 Model Planner

When presets and recognized plans do not match, `plan_actions()` calls an OpenAI-compatible Chat Completions endpoint:

```text
POST {API_BASE}/chat/completions
```

The request includes:

- `model`
- `messages`
- `temperature`
- `max_tokens`

`SYSTEM_PROMPT` requires a JSON-only action array. `_json_content()` tolerates fenced JSON and extra text by extracting the outer JSON array or object. `_parse_actions()` also accepts `action` as an alias for `type`.

Validation rules:

- The response must be a list or an object with `actions`.
- At least one executable action is required; `ask_user` and `finish` do not count.
- Every action is passed through `assert_safe_action()` before execution.

If the request fails, the response shape is invalid, or safety validation fails, `plan_actions()` raises a planner error and the runner marks the run failed.

## 6. Browser Execution

`apps/server/app/agent/browser.py` defines the abstract `BrowserSession` and the current `PlaywrightBrowserSession`.

### 6.1 Session Creation

`create_browser_session(settings)`:

1. Dynamically imports `playwright.async_api.async_playwright`.
2. Starts Playwright.
3. When `BROWSER_HEADLESS=true`, launches Chromium with `playwright.chromium.launch(headless=True)`.
4. When `BROWSER_HEADLESS=false`, starts an independent Chromium process and connects over CDP; after the run, Playwright detaches without closing that Chromium process.
5. Creates a page using the configured viewport.
6. Returns `PlaywrightBrowserSession`.

If import, startup, or Chromium launch fails, it raises `RuntimeError`. The runner catches that and marks the run as `execution_failed`.

### 6.2 Action Execution

`execute()` dispatches by `action.type`:

- `goto`: `page.goto(..., wait_until="domcontentloaded")`.
- `fill`: build candidate selectors and call `_try_fill()`.
- `click`: try selectors first, then role-based link/button locators.
- `press`: support aliases for `return`, `enter`, and `esc`.
- `scroll`: use mouse wheel.
- `wait`: wait for the configured number of milliseconds.
- `extract`: wait for the page to settle, then call an extractor based on target or URL.

Before extraction, `_wait_for_page_settle()` attempts `domcontentloaded`, `load`, and `networkidle`. Failures are ignored because many real websites keep long-lived requests open.

### 6.3 Extractors

Built-in extractors cover:

- Hacker News top story and story lists.
- GitHub Trending repositories.
- Wikipedia Python summary and generic article summary.
- MDN Web API overview and Fetch API details.
- httpbin form echo.
- Generic page summary.

Extractors run JavaScript in the page through `page.evaluate()`. `_evaluate()` retries when the execution context is destroyed during navigation or refresh.

### 6.4 Screenshots

After each successful action, the runner writes a screenshot:

```text
{run_id}_{action_index:02d}.png
```

Screenshots are saved under `ARTIFACTS_DIR` and loaded by the frontend through `/artifacts/{file_name}`.

## 7. Safety Boundary

`apps/server/app/agent/safety.py` uses keyword checks to block risky actions.

Current `RISKY_TERMS` include:

- Payment, checkout, order submission, and add-to-cart flows.
- Account deletion and password changes.
- Captcha and 2FA.
- Credit cards, passwords, and sensitive information.
- Private file upload.
- Several Chinese risk terms.

`DISALLOWED_MOCK_TERMS` blocks the old Aurora/mock shopping flow:

- `aurora task lamp`
- `mock/findparts`
- `localhost:8000/mock`
- `127.0.0.1:8000/mock`

This is a conservative local-demo guard. It is not a production permission model, user-confirmation system, or complete risk engine.

## 8. Local Storage and Events

### 8.1 RunsStore

`apps/server/app/storage/runs_store.py` is the backend state center:

- Loads historical runs from JSON at startup.
- Writes every mutation back to JSON.
- Keeps per-run SSE subscriber queues.
- Publishes `RunEvent` objects as part of state updates.

Core methods:

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

This storage layer is suitable for single-process local development. It has no transactions, locks, user isolation, or cross-process synchronization.

### 8.2 Server-Sent Events

`GET /api/runs/{run_id}/events` returns `text/event-stream`.

The first message is always a full:

```text
type=snapshot
```

The snapshot includes the full `run` for initial load and reconnect. Later events include:

| type | Meaning |
| --- | --- |
| `chat_message` | A chat message was appended. |
| `timeline_step` | A timeline step was added or replaced. |
| `screenshot` | A new screenshot is available. |
| `status` | Run status changed. |
| `extracted` | Structured extraction output changed. |

Most events include a complete `run`. The frontend store prefers `event.run` when present to avoid inconsistent local merges.

## 9. API Reference

### 9.1 Health Check

```http
GET /health
```

Response:

```json
{"status":"ok","app":"navora-lite"}
```

### 9.2 Create Run

```http
POST /api/runs
Content-Type: application/json
```

Request:

```json
{
  "task": "Open Hacker News and extract the current top story.",
  "url": "https://news.ycombinator.com/",
  "auto_start": true,
  "preset_id": "hn-top-story"
}
```

Response:

```json
{
  "run_id": "run_xxxxxxxxxxxxxxxxxx",
  "status": "running"
}
```

Notes:

- `auto_start=false` creates an idle run.
- `preset_id` is optional.
- `auto_start=true` without `preset_id` requires model settings.

### 9.3 List Runs

```http
GET /api/runs
```

Returns `Run[]`, sorted by `startedAt` descending.

### 9.4 Get Run

```http
GET /api/runs/{run_id}
```

Returns a full `Run`. Missing runs return 404.

### 9.5 Stop Run

```http
POST /api/runs/{run_id}/stop
```

Returns the updated `Run`. Missing runs return 404.

### 9.6 Rerun

```http
POST /api/runs/{run_id}/rerun
```

Returns a new `CreateRunResponse`. The backend copies the old task, URL, and preset metadata.

### 9.7 SSE Events

```http
GET /api/runs/{run_id}/events
```

Each message is formatted as:

```text
data: {...}
```

### 9.8 Task History

```http
GET /api/tasks
DELETE /api/tasks/{run_id}
```

`GET /api/tasks` returns run history from the same store as `/api/runs`. `DELETE` removes the local history item and subscriber set.

### 9.9 Settings

```http
GET /api/settings
POST /api/settings
```

`GET` returns current settings. A non-empty `API_KEY` is masked as `********`.

`POST`:

1. Serializes the payload.
2. Writes the current working directory's `.env`.
3. Preserves unrelated `.env` lines.
4. Does not overwrite an existing key when incoming `API_KEY` is `********`.
5. Clears the `get_settings()` cache.
6. Returns refreshed settings.

## 10. Frontend Architecture

### 10.1 Pages

`apps/web/src/app` uses the Next.js App Router:

- `/`: redirects to `/new-chat`.
- `/new-chat`: free-form task entry page with model-config validation.
- `/runs/[runId]`: run detail page that loads the run and subscribes to SSE.
- `/tasks`: task history and preset demos.
- `/sessions`: current browser session overview.
- `/settings`: display theme and model settings.
- `/agents`: redirects to `/tasks`.

### 10.2 API Client

`apps/web/src/lib/api.ts` uses:

```text
NEXT_PUBLIC_API_BASE || http://localhost:8000
```

Main functions:

- `getRun`
- `getTasks`
- `deleteTask`
- `createRun`
- `stopRun`
- `rerun`
- `getSettings`
- `saveSettings`

`request()` prefers backend JSON `detail` as the error message. A 204 response returns `undefined`.

### 10.3 SSE Client

`apps/web/src/lib/events.ts` uses the browser's native `EventSource`. SSE is used only for backend-to-frontend updates; control actions such as stop, rerun, and delete still use HTTP APIs.

### 10.4 State Management

`apps/web/src/lib/store.ts` uses Zustand for:

- `run`: current run, initialized with bundled `sampleRun`.
- `activeTab`: current RunTabs tab.
- `apiOnline`: backend connection status.
- `applyEvent(event)`: SSE event merge logic.

If an event includes a full `run`, the store replaces local state with it. Otherwise, it updates messages, timeline, status, and extraction output by event type.

### 10.5 UI Components

Core components under `apps/web/src/components`:

- `app-sidebar.tsx`: navigation, task stats, and failure-type counts.
- `chat-panel.tsx`, `chat-message.tsx`: task conversation and checklist.
- `browser-preview.tsx`, `fullscreen-preview-dialog.tsx`: screenshot preview and fullscreen mode.
- `execution-timeline.tsx`: step timeline and screenshot selection.
- `extracted-information.tsx`: structured JSON display and copy action.
- `run-header.tsx`: run metadata, export, rerun, and API example modal.
- `run-tabs.tsx`: Overview, Output, Inputs, Recording, and Code tabs.
- `model-settings-dialog.tsx`: model configuration modal.
- `status-badge.tsx`: visual status mapping.
- `theme-provider.tsx`: theme initialization and cross-component synchronization.

### 10.6 Themes

Themes are controlled by CSS variables and `data-theme`:

- `deep-blue`
- `light`
- `warm`

`theme.ts` persists the selected theme in `localStorage` and broadcasts a `navora-theme-change` event to mounted components.

## 11. Development and Verification

### 11.1 Backend Tests

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\server"
.\.venv\Scripts\python.exe -m pytest
```

Without a virtual environment:

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\server"
python -m pytest
```

Current tests cover:

- Planner JSON parsing, fenced JSON, and `action` alias handling.
- Disabled mock flow protection.
- Common recognized task plans.
- Blocked and empty extraction-result detection.
- Preset planner output.
- Runner handling of planner fallback failure.
- Runs API create, read, stop, and related behavior.
- Tasks API list and delete behavior.
- Safety guard behavior.

### 11.2 Frontend Build

```powershell
cd "E:\codex\Navora Lite\navora-lite\apps\web"
pnpm.cmd build
```

### 11.3 CLI Verification

The CLI creates a free-form run, so configure a model first:

```powershell
cd "E:\codex\Navora Lite\navora-lite"
python scripts/run_demo.py `
  --task "Open Hacker News and extract the current top story with its source, score, age, and comments." `
  --url "https://news.ycombinator.com/"
```

Without model settings, start a preset from the frontend Tasks page.

## 12. Extension Guide

### 12.1 Add a New Action

Update:

1. `apps/server/app/agent/actions.py`: extend `AgentAction.type` and description logic.
2. `apps/server/app/agent/browser.py`: implement dispatch in `PlaywrightBrowserSession.execute()`.
3. `apps/server/app/agent/safety.py`: evaluate safety implications.
4. `apps/server/app/llm/prompts.py`: teach the model the output format.
5. `apps/web/src/lib/types.ts`: update frontend types if timeline or event shape changes.
6. `apps/server/tests`: add planner, runner, or safety tests.

### 12.2 Add a Preset

Update:

1. `apps/server/app/agent/presets.py`: add a `PRESET_TASKS` entry.
2. `apps/web/src/lib/preset-tasks.ts`: add the frontend preset card data.
3. `apps/web/src/app/tasks/page.tsx`: add an icon mapping if needed.
4. `apps/server/tests/test_planner.py`: verify the preset action sequence.

### 12.3 Integrate Real Websites

Recommended approach:

- Prefer stable selectors in model output.
- Keep browser actions coarse for search, navigation, and extraction.
- Add site-specific extractors for important targets instead of relying entirely on generic page summary.
- Add explicit user confirmation for login, payment, submit, upload, or other sensitive actions instead of weakening the keyword guard.

### 12.4 Replace Storage

If replacing `RunsStore` with a database, preserve:

- Run CRUD.
- Atomic update semantics for timeline, messages, screenshots, and extracted output.
- Status and controlStatus coupling.
- SSE event publication.
- Subscriber or message-channel cleanup when history is deleted.

For multi-process or multi-instance deployments, replace in-process SSE queues with Redis Pub/Sub, database notifications, or a message queue.

## 13. Current Limitations

- Local JSON storage is not suitable for multi-user, multi-instance, or high-concurrency deployments.
- There is no authentication, user isolation, or permission model.
- Stopping a run takes effect only at action boundaries.
- `BROWSER_CHANNEL` is not passed to Playwright as a launch channel.
- There is no mock browser fallback when Playwright launch fails.
- Free-form tasks still need model settings even when they could match `recognized_task_plan()`.
- Safety checks are keyword guards, not production-grade risk controls.
- The settings API writes `.env` in the current working directory, so deployment must ensure the backend starts from the intended path.
- The frontend `sampleRun` is only an initial no-backend display and is not live data.
