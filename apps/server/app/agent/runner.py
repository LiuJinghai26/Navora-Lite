import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.agent.actions import AgentAction, describe_action
from app.agent.browser import create_browser_session
from app.agent.safety import assert_safe_action
from app.config import Settings
from app.llm.client import plan_actions
from app.models import ChatMessage, ChecklistItem, ScreenshotItem, TimelineStep
from app.storage.runs_store import RunsStore


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ms_since(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def artifact_url(settings: Settings, path: Path) -> str:
    return f"/artifacts/{path.name}"


def step_to_checklist(action: AgentAction) -> str:
    if action.type == "goto":
        return "Open mock FindItParts page"
    if action.type == "fill" and (action.target or "").lower() == "search input":
        return 'Searching for product "FIRESTONE W01-377-8537"'
    if action.type == "click" and "product" in (action.target or "").lower():
        return "Open product page and locate item"
    if action.type == "fill" and (action.target or "").lower() == "quantity":
        return "Set quantity to 1"
    if action.type == "click" and (action.target or "").lower() == "add to cart":
        return "Added product to cart with quantity 1"
    if action.type == "click" and (action.target or "").lower() == "cart":
        return "Open cart page"
    if action.type == "extract":
        return "Extract quantity from cart"
    return describe_action(action)


async def run_agent(run_id: str, store: RunsStore, settings: Settings) -> None:
    run = store.get_run(run_id)
    if run is None:
        return

    # Set status before planning so the UI can show immediate control feedback.
    run.status = "running"
    run.controlStatus = "controlling"
    run.startedAt = now_iso()
    store.set_status(run_id, "running")

    planner = await plan_actions(run.task, run.url, settings)
    run = store.get_run(run_id)
    if run is None:
        return
    run.fallbackReason = planner.fallback_reason
    store.update_run(run)

    if planner.fallback_reason:
        # Surface planner fallback in both chat and timeline instead of hiding it in logs.
        store.add_message(
            run_id,
            ChatMessage(
                id=f"msg_{uuid4().hex[:10]}",
                role="system",
                content=planner.fallback_reason,
                createdAt=now_iso(),
            ),
        )
        store.add_step(
            run_id,
            TimelineStep(
                id=f"step_{uuid4().hex[:10]}",
                index=0,
                action="fallback",
                description=planner.fallback_reason,
                status="success",
                startedAt=now_iso(),
                endedAt=now_iso(),
                durationMs=0,
            ),
        )

    checklist = [ChecklistItem(text=step_to_checklist(action), status="pending") for action in planner.actions]
    store.add_message(
        run_id,
        ChatMessage(
            id=f"msg_{uuid4().hex[:10]}",
            role="assistant",
            content="On it. I will search for the product, add it to the cart with quantity 1, then extract the cart quantity.",
            createdAt=now_iso(),
            checklist=checklist,
        ),
    )

    session = await create_browser_session(settings)
    run_started = time.perf_counter()
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
                if action.type == "extract":
                    store.set_extracted(run_id, result)
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
                content="Done. The product has been added and the quantity is 1.",
                createdAt=now_iso(),
            ),
        )
    finally:
        await session.close()


async def _mark_stopped(run_id: str, store: RunsStore) -> None:
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
