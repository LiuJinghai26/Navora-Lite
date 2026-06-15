from datetime import datetime, timezone
import re
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.agent.presets import PRESET_TASKS
from app.agent.runner import run_agent
from app.config import get_settings
from app.llm.client import has_planner_config
from app.models import ChatMessage, CreateRunRequest, CreateRunResponse, Run

router = APIRouter(prefix="/api/runs", tags=["runs"])
DISABLED_MOCK_URL = "http://localhost:8000/mock/findparts"


def _title_for_task(task: str, preset_id: str | None = None) -> str:
    # Prefer stable product titles for known presets, otherwise keep the full task text.
    if preset_id and preset_id in PRESET_TASKS:
        return str(PRESET_TASKS[preset_id]["title"])
    if "HACKER NEWS" in task.upper():
        return "Hacker News Top Story"
    if "WIKIPEDIA" in task.upper() and "PYTHON" in task.upper():
        return "Wikipedia Python Summary"
    if "MDN" in task.upper():
        return "MDN Web API Research"
    return task.strip() or "Browser Agent Run"


def _now() -> str:
    # UTC keeps persisted runs independent from the developer machine timezone.
    return datetime.now(timezone.utc).isoformat()


def _start_url_for_task(task: str, url: str) -> str:
    # Task text can contain the only useful URL when the form starts empty.
    match = re.search(r"https?://[^\s`，。；,;]+", task)
    if match and (not url or url == DISABLED_MOCK_URL):
        return match.group(0).rstrip(").]")
    if url == DISABLED_MOCK_URL:
        return ""
    return url


@router.post("", response_model=CreateRunResponse)
async def create_run(payload: CreateRunRequest, request: Request, background_tasks: BackgroundTasks) -> CreateRunResponse:
    # Free-form auto-start runs need model settings; presets are the model-free path.
    store = request.app.state.runs_store
    settings = get_settings()
    start_url = _start_url_for_task(payload.task, payload.url)
    if payload.auto_start and not payload.preset_id and not has_planner_config(settings):
        raise HTTPException(status_code=400, detail="请先在 Settings 中配置模型 API，再启动浏览器任务。")
    run_id = f"run_{uuid4().hex[:18]}"
    run = Run(
        id=run_id,
        title=_title_for_task(payload.task, payload.preset_id),
        task=payload.task,
        url=start_url,
        status="idle",
        controlStatus="idle",
        inputs={
            "task": payload.task,
            "url": start_url,
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
    # Rerun creates a fresh run record so the original history item remains immutable.
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
