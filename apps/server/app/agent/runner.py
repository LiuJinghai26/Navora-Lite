import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.agent.actions import AgentAction, describe_action
from app.agent.browser import create_browser_session
from app.agent.safety import assert_safe_action
from app.config import Settings
from app.llm.client import plan_actions
from app.llm.schemas import PlannerConfigurationError, PlannerError, TaskRecognitionError
from app.models import ChatMessage, ChecklistItem, FailureType, ScreenshotItem, TimelineStep
from app.storage.runs_store import RunsStore


BLOCKED_EXTRACTION_MARKERS = (
    "just a moment",
    "client challenge",
    "verify you are human",
    "verifies you are not a bot",
    "robot or human",
    "are you a robot",
    "captcha",
    "access denied",
    "request blocked",
    "请求被拦截",
    "enter the characters seen in the image",
)

OPEN_BROWSER_SESSIONS: list[Any] = []


def now_iso() -> str:
    # Store timestamps as UTC ISO strings for easy JSON persistence and frontend formatting.
    return datetime.now(timezone.utc).isoformat()


def ms_since(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def artifact_url(settings: Settings, path: Path) -> str:
    # FastAPI serves artifact files from the mounted /artifacts route.
    return f"/artifacts/{path.name}"


def step_to_checklist(action: AgentAction) -> str:
    # Checklist text is friendlier than raw planner action names in the chat transcript.
    if action.type == "goto":
        return f"Open {action.url or 'the target page'}"
    if action.type == "wait":
        return action.condition or "Wait for the page to settle"
    if action.type == "extract" and action.target:
        return f"Extract {action.target}"
    if action.type == "fill" and (action.target or "").lower() == "search input":
        return f'Search for "{action.value or "the query"}"'
    if action.type == "click" and "product" in (action.target or "").lower():
        return "Open product page and locate item"
    if action.type == "click" and "color" in (action.target or "").lower():
        return "Choose the requested product color"
    if action.type == "fill" and (action.target or "").lower() == "quantity":
        return f"Set quantity to {action.value or 'the requested amount'}"
    if action.type == "extract":
        return "Extract requested information"
    return describe_action(action)


async def close_or_keep_browser_session(session: Any, settings: Settings) -> None:
    if settings.browser_headless:
        await session.close()
        return
    # Visible browser runs detach Playwright control but keep Chromium alive for inspection.
    await session.keep_open()
    OPEN_BROWSER_SESSIONS.append(session)


def run_agent(run_id: str, store: RunsStore, settings: Settings) -> None:
    # Uvicorn can run a Windows Selector loop, so browser work gets its own loop.
    loop = _new_browser_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_run_agent_async(run_id, store, settings))
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            asyncio.set_event_loop(None)
            loop.close()


def _new_browser_loop() -> asyncio.AbstractEventLoop:
    if sys.platform == "win32":
        return asyncio.WindowsProactorEventLoopPolicy().new_event_loop()
    return asyncio.new_event_loop()


async def _run_agent_async(run_id: str, store: RunsStore, settings: Settings) -> None:
    run = store.get_run(run_id)
    if run is None:
        return

    # Set status before planning so the UI can show immediate control feedback.
    run.status = "running"
    run.controlStatus = "controlling"
    run.startedAt = now_iso()
    store.set_status(run_id, "running")
    run_started = time.perf_counter()

    preset_id = run.inputs.get("preset_id")
    try:
        planner = await plan_actions(run.task, run.url, settings, preset_id=str(preset_id) if preset_id else None)
    except TaskRecognitionError as exc:
        _mark_failed(run_id, store, "recognition_failed", "recognition", str(exc), run_started)
        return
    except (PlannerConfigurationError, PlannerError) as exc:
        _mark_failed(run_id, store, "planning_failed", "planning", str(exc), run_started)
        return

    run = store.get_run(run_id)
    if run is None:
        return
    if planner.fallback_reason:
        _mark_failed(run_id, store, "planning_failed", "planning", planner.fallback_reason, run_started)
        return

    run.fallbackReason = None
    store.update_run(run)

    checklist = [ChecklistItem(text=step_to_checklist(action), status="pending") for action in planner.actions]
    store.add_message(
        run_id,
        ChatMessage(
            id=f"msg_{uuid4().hex[:10]}",
            role="assistant",
            content="On it. I will follow the preset browser steps, capture screenshots, and extract the requested information.",
            createdAt=now_iso(),
            checklist=checklist,
        ),
    )

    try:
        session = await create_browser_session(settings)
    except Exception as exc:
        _mark_failed(run_id, store, "execution_failed", "browser", str(exc), run_started)
        return

    if hasattr(session, "context"):
        session.context["planned_click_targets"] = [action.target for action in planner.actions if action.type == "click" and action.target]

    extracted_payload: Any | None = None
    try:
        for action_index, action in enumerate(planner.actions, start=1):
            run = store.get_run(run_id)
            if run is None or run.stopRequested:
                await _mark_stopped(run_id, store)
                return

            # Publish a running step first, then replace it with the terminal state after execution.
            step = TimelineStep(
                id=f"step_{uuid4().hex[:10]}",
                index=action_index,
                action=action.type,
                description=describe_action(action),
                status="running",
                startedAt=now_iso(),
            )
            store.add_step(run_id, step)
            start = time.perf_counter()
            try:
                assert_safe_action(action)
                result = await session.execute(action)
                extraction_failure = None
                if action.type == "extract":
                    extracted_payload = _updated_extraction_payload(extracted_payload, action, result)
                    store.set_extracted(run_id, extracted_payload)
                    extraction_failure = _extraction_failure_message(result)
                screenshot_path = settings.artifacts_dir / f"{run_id}_{action_index:02d}.{'png' if session.__class__.__name__.startswith('Playwright') else 'svg'}"
                await session.screenshot(screenshot_path, step.description)
                # Screenshots drive both Browser Preview and the Recording tab.
                shot = ScreenshotItem(
                    id=f"shot_{uuid4().hex[:10]}",
                    title=step.description,
                    imageUrl=artifact_url(settings, screenshot_path),
                    createdAt=now_iso(),
                )
                store.add_screenshot(run_id, shot)
                step.screenshotUrl = shot.imageUrl
                if extraction_failure:
                    raise RuntimeError(extraction_failure)
                step.status = "success"
                step.endedAt = now_iso()
                step.durationMs = ms_since(start)
                store.replace_step(run_id, step)
            except Exception as exc:
                step.status = "failed"
                step.error = str(exc)
                step.endedAt = now_iso()
                step.durationMs = ms_since(start)
                store.replace_step(run_id, step)
                run = store.get_run(run_id)
                if run:
                    run.finishedAt = now_iso()
                    run.durationMs = ms_since(run_started)
                    run.failureType = "execution_failed"
                    store.update_run(run)
                store.set_status(run_id, "failed")
                store.add_message(
                    run_id,
                    ChatMessage(
                        id=f"msg_{uuid4().hex[:10]}",
                        role="assistant",
                        content=f"I could not finish this run: {exc}",
                        createdAt=now_iso(),
                    ),
                )
                return
            await asyncio.sleep(settings.runner_step_delay_seconds)

        run = store.get_run(run_id)
        if run:
            run.finishedAt = now_iso()
            run.durationMs = ms_since(run_started)
            store.update_run(run)
        store.set_status(run_id, "completed")
        store.add_message(
            run_id,
            ChatMessage(
                id=f"msg_{uuid4().hex[:10]}",
                role="assistant",
                content="Done. The preset browser task finished and the extracted data is ready.",
                createdAt=now_iso(),
            ),
        )
    finally:
        await close_or_keep_browser_session(session, settings)


def _updated_extraction_payload(current: Any | None, action: AgentAction, result: Any) -> Any:
    if current is None:
        return result

    entry = {"target": action.target or "Extracted information", "data": result}
    if isinstance(current, dict) and isinstance(current.get("extracts"), list):
        return {
            **current,
            "latest": result,
            "extracts": [*current["extracts"], entry],
        }
    return {
        "latest": result,
        "extracts": [
            {"target": "Previous extract", "data": current},
            entry,
        ],
    }


def _extraction_failure_message(result: Any) -> str | None:
    if not isinstance(result, dict):
        return None

    # Treat bot walls and empty generic summaries as execution failures, not successful extracts.
    content = json.dumps(result, ensure_ascii=False).casefold()
    if any(marker in content for marker in BLOCKED_EXTRACTION_MARKERS):
        return "The site blocked automated browsing or showed a verification page."
    if "best buy international: select your country" in content or "choose a country" in content:
        return "The site showed an interstitial country selector instead of the requested results."
    if _is_empty_page_summary(result):
        return "The page did not expose extractable content for this task."
    return None


def _is_empty_page_summary(result: dict[str, Any]) -> bool:
    # Generic page summaries should contain at least one user-visible signal.
    if not {"page_title", "url", "paragraphs", "headings", "links"}.issubset(result):
        return False

    title = str(result.get("page_title") or "").strip()
    heading = str(result.get("heading") or "").strip()
    paragraphs = result.get("paragraphs") or []
    headings = result.get("headings") or []
    links = result.get("links") or []
    return bool(title) and not heading and not paragraphs and not headings and not links


def _mark_failed(run_id: str, store: RunsStore, failure_type: FailureType, action: str, error: str, started_at: float) -> None:
    # Planning and recognition failures still get a timeline row so the UI has context.
    step = TimelineStep(
        id=f"step_{uuid4().hex[:10]}",
        index=0,
        action=action,
        description=error,
        status="failed",
        startedAt=now_iso(),
        endedAt=now_iso(),
        durationMs=0,
        error=error,
    )
    store.add_step(run_id, step)
    run = store.get_run(run_id)
    if run:
        run.finishedAt = now_iso()
        run.durationMs = ms_since(started_at)
        run.failureType = failure_type
        store.update_run(run)
    store.set_status(run_id, "failed")
    store.add_message(
        run_id,
        ChatMessage(
            id=f"msg_{uuid4().hex[:10]}",
            role="assistant",
            content=f"I could not plan this run: {error}",
            createdAt=now_iso(),
        ),
    )


async def _mark_stopped(run_id: str, store: RunsStore) -> None:
    # Stopped runs use a synthetic final step because the user action happens outside the browser.
    store.set_status(run_id, "stopped")
    store.add_step(
        run_id,
        TimelineStep(
            id=f"step_{uuid4().hex[:10]}",
            index=999,
            action="stop",
            description="Run stopped by user",
            status="stopped",
            startedAt=now_iso(),
            endedAt=now_iso(),
            durationMs=0,
        ),
    )
    store.add_message(
        run_id,
        ChatMessage(
            id=f"msg_{uuid4().hex[:10]}",
            role="assistant",
            content="The browser control run has been stopped.",
            createdAt=now_iso(),
        ),
    )
