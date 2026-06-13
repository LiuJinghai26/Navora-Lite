from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.agent.presets import PRESET_TASKS
from app.agent.runner import run_agent
from app.config import get_settings
from app.models import ChatMessage, CreateRunRequest, CreateRunResponse, Run

router = APIRouter(prefix="/api/runs", tags=["runs"])


def _title_for_task(task: str, preset_id: str | None = None) -> str:
    if preset_id and preset_id in PRESET_TASKS:
        return str(PRESET_TASKS[preset_id]["title"])
    if "HACKER NEWS" in task.upper():
        return "Hacker News Top Story"
    if "WIKIPEDIA" in task.upper() and "PYTHON" in task.upper():
        return "Wikipedia Python Summary"
    if "MDN" in task.upper():
        return "MDN Web API Research"
    if "AURORA TASK LAMP" in task.upper():
        return "Configure Desk Lamp Cart"
    return task.strip()[:72] or "Browser Agent Run"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("", response_model=CreateRunResponse)
async def create_run(payload: CreateRunRequest, request: Request, background_tasks: BackgroundTasks) -> CreateRunResponse:
    store = request.app.state.runs_store
    settings = get_settings()
    run_id = f"run_{uuid4().hex[:18]}"
    run = Run(
        id=run_id,
        title=_title_for_task(payload.task, payload.preset_id),
        task=payload.task,
        url=payload.url,
        status="idle",
        controlStatus="idle",
        inputs={
            "task": payload.task,
            "url": payload.url,
            "model": settings.model_name,
            "browser": settings.browser_channel,
            "preset_id": payload.preset_id,
        },
        messages=[
            ChatMessage(
                id=f"msg_{uuid4().hex[:10]}",
                role="user",
                content=payload.task,
                createdAt=_now(),
            )
        ],
    )
    store.create_run(run)
    if payload.auto_start:
        # FastAPI runs the browser task after the response, keeping run creation snappy.
        background_tasks.add_task(run_agent, run_id, store, settings)
    return CreateRunResponse(run_id=run_id, status="running" if payload.auto_start else "idle")


@router.get("", response_model=list[Run])
async def list_runs(request: Request) -> list[Run]:
    return request.app.state.runs_store.list_runs()


@router.get("/{run_id}", response_model=Run)
async def get_run(run_id: str, request: Request) -> Run:
    run = request.app.state.runs_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/stop", response_model=Run)
async def stop_run(run_id: str, request: Request) -> Run:
    run = request.app.state.runs_store.request_stop(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/rerun", response_model=CreateRunResponse)
async def rerun(run_id: str, request: Request, background_tasks: BackgroundTasks) -> CreateRunResponse:
    old_run = request.app.state.runs_store.get_run(run_id)
    if old_run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    preset_id = old_run.inputs.get("preset_id")
    payload = CreateRunRequest(
        task=old_run.task,
        url=old_run.url,
        auto_start=True,
        preset_id=str(preset_id) if preset_id else None,
    )
    response = await create_run(payload, request, background_tasks)
    return response
