import asyncio
import json
from pathlib import Path
from typing import Any

from app.models import ChatMessage, Run, RunEvent, ScreenshotItem, TimelineStep


def _to_dict(model: Any) -> dict[str, Any]:
    # Support Pydantic v2 while keeping this helper harmless for v1-style models.
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()


class RunsStore:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._runs: dict[str, Run] = {}
        self._subscribers: dict[str, set[asyncio.Queue[RunEvent]]] = {}
        self._load()

    def _load(self) -> None:
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
        data = {"runs": [_to_dict(run) for run in self._runs.values()]}
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_runs(self) -> list[Run]:
        return sorted(self._runs.values(), key=lambda run: run.startedAt or "", reverse=True)

    def create_run(self, run: Run) -> Run:
        self._runs[run.id] = run
        self._save()
        return run

    def get_run(self, run_id: str) -> Run | None:
        return self._runs.get(run_id)

    def delete_run(self, run_id: str) -> Run | None:
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
        for queue in list(self._subscribers.get(run_id, set())):
            queue.put_nowait(event)

    async def subscribe(self, run_id: str):
        queue: asyncio.Queue[RunEvent] = asyncio.Queue()
        self._subscribers.setdefault(run_id, set()).add(queue)
        try:
            yield queue
        finally:
            self._subscribers.get(run_id, set()).discard(queue)
