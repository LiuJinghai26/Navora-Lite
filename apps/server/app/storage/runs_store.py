import asyncio
import json
from pathlib import Path
from typing import Any

from app.models import ChatMessage, Run, RunEvent, ScreenshotItem, TimelineStep


Subscriber = tuple[asyncio.AbstractEventLoop, asyncio.Queue[RunEvent]]


def _to_dict(model: Any) -> dict[str, Any]:
    # Support Pydantic v2 while keeping this helper harmless for v1-style models.
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()


class RunsStore:
    def __init__(self, storage_path: Path):
        # Keep all run state in memory, with JSON persistence after each mutation.
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._runs: dict[str, Run] = {}
        self._subscribers: dict[str, set[Subscriber]] = {}
        self._load()

    def _load(self) -> None:
        # Corrupt local state should not prevent the dev server from starting.
        if not self.storage_path.exists():
            return
        try:
            payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        for item in payload.get("runs", []):
            run = Run(**item)
            self._runs[run.id] = run

    def _save(self) -> None:
        # A single JSON file is enough for local development and demos.
        data = {"runs": [_to_dict(run) for run in self._runs.values()]}
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_runs(self) -> list[Run]:
        # Most recent started runs should appear first in the task history.
        return sorted(self._runs.values(), key=lambda run: run.startedAt or "", reverse=True)

    def create_run(self, run: Run) -> Run:
        self._runs[run.id] = run
        self._save()
        return run

    def get_run(self, run_id: str) -> Run | None:
        return self._runs.get(run_id)

    def delete_run(self, run_id: str) -> Run | None:
        # Drop subscribers too so deleted history items stop receiving events.
        run = self._runs.pop(run_id, None)
        if run is None:
            return None
        self._subscribers.pop(run_id, None)
        self._save()
        return run

    def update_run(self, run: Run, event: RunEvent | None = None) -> Run:
        self._runs[run.id] = run
        self._save()
        if event is not None:
            # Every persisted mutation can also fan out to live SSE subscribers.
            self.publish(run.id, event)
        return run

    def add_message(self, run_id: str, message: ChatMessage) -> None:
        run = self._runs[run_id]
        run.messages.append(message)
        self.update_run(run, RunEvent(type="chat_message", message=message, run=run))

    def add_step(self, run_id: str, step: TimelineStep) -> None:
        run = self._runs[run_id]
        run.timeline.append(step)
        self.update_run(run, RunEvent(type="timeline_step", step=step, run=run))

    def replace_step(self, run_id: str, step: TimelineStep) -> None:
        run = self._runs[run_id]
        for index, existing in enumerate(run.timeline):
            if existing.id == step.id:
                run.timeline[index] = step
                break
        else:
            run.timeline.append(step)
        self.update_run(run, RunEvent(type="timeline_step", step=step, run=run))

    def add_screenshot(self, run_id: str, screenshot: ScreenshotItem) -> None:
        run = self._runs[run_id]
        run.screenshots.append(screenshot)
        self.update_run(run, RunEvent(type="screenshot", image_url=screenshot.imageUrl, run=run))

    def set_status(self, run_id: str, status: str) -> None:
        # controlStatus mirrors run status for the browser-control UI.
        run = self._runs[run_id]
        run.status = status  # type: ignore[assignment]
        if status == "running":
            run.controlStatus = "controlling"
        elif status == "completed":
            run.controlStatus = "completed"
        elif status == "stopped":
            run.controlStatus = "stopped"
        elif status == "failed":
            run.controlStatus = "failed"
        self.update_run(run, RunEvent(type="status", status=run.status, run=run))

    def set_extracted(self, run_id: str, data: Any) -> None:
        run = self._runs[run_id]
        run.extracted = data
        self.update_run(run, RunEvent(type="extracted", data=data, run=run))

    def request_stop(self, run_id: str) -> Run | None:
        # The runner observes stopRequested at action boundaries.
        run = self._runs.get(run_id)
        if run is None:
            return None
        run.stopRequested = True
        if run.status == "running":
            run.status = "stopped"
            run.controlStatus = "stopped"
        self.update_run(run, RunEvent(type="status", status=run.status, run=run))
        return run

    def publish(self, run_id: str, event: RunEvent) -> None:
        # Queues decouple the runner from slow or disconnected browser clients.
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None
        subscribers = self._subscribers.get(run_id, set())
        stale: list[Subscriber] = []
        for loop, queue in list(subscribers):
            if loop.is_closed():
                stale.append((loop, queue))
                continue
            if running_loop is loop:
                queue.put_nowait(event)
                continue
            try:
                loop.call_soon_threadsafe(queue.put_nowait, event)
            except RuntimeError:
                stale.append((loop, queue))
        for subscriber in stale:
            subscribers.discard(subscriber)

    async def subscribe(self, run_id: str):
        # Each client gets its own queue so slow consumers do not block other clients.
        queue: asyncio.Queue[RunEvent] = asyncio.Queue()
        subscriber = (asyncio.get_running_loop(), queue)
        self._subscribers.setdefault(run_id, set()).add(subscriber)
        try:
            yield queue
        finally:
            self._subscribers.get(run_id, set()).discard(subscriber)
