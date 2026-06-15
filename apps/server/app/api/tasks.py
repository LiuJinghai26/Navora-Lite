from pathlib import Path
import json
import threading
from typing import Any, NamedTuple
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status

from app.api.runs import _now, _start_url_for_task, _title_for_task
from app.agent.runner import run_agent
from app.config import get_settings
from app.models import BatchPromptSource, ChatMessage, CreateBatchTasksRequest, CreateBatchTasksResponse, Run

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
BATCH_ALL_SOURCE = "all"
BATCH_RUN_LOCK = threading.Lock()

BATCH_PROMPT_FILES = (
    "browser_task_prompts_60.json",
    "browser_task_prompts_60_no_url.json",
    "browser_multistep_prompts_20.json",
)


class PromptItem(NamedTuple):
    source: str
    number: int
    task: str
    section: str
    section_title: str = ""


class PromptSection(NamedTuple):
    slug: str
    title: str
    count: int


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _prompt_path(file_name: str) -> Path:
    if file_name not in BATCH_PROMPT_FILES:
        raise HTTPException(status_code=400, detail="Unknown batch prompt source")
    path = _repo_root() / file_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Batch prompt file not found")
    return path


def _load_prompt_suite(file_name: str) -> dict[str, Any]:
    try:
        return json.loads(_prompt_path(file_name).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Batch prompt file is invalid JSON") from exc


def _split_prompt_source(source: str) -> tuple[str, str | None]:
    if source == BATCH_ALL_SOURCE:
        raise HTTPException(status_code=400, detail="Unknown batch prompt source")
    file_name, _, section = source.partition("#")
    if file_name not in BATCH_PROMPT_FILES:
        raise HTTPException(status_code=400, detail="Unknown batch prompt source")
    return file_name, section or None


def _suite_title(file_name: str, suite: dict[str, Any]) -> str:
    return str(suite.get("title") or Path(file_name).stem)


def _prompt_items_from_suite(source: str, suite: dict[str, Any]) -> list[PromptItem]:
    prompts: list[PromptItem] = []
    for section in suite.get("sections", []):
        section_slug = str(section["slug"])
        section_title = str(section.get("title") or section_slug)
        for prompt in section.get("prompts", []):
            task = " ".join(str(prompt["task"]).split()).strip()
            if task:
                prompts.append(PromptItem(source, int(prompt["number"]), task, section_slug, section_title))
    return prompts


def _prompt_section_summaries(suite: dict[str, Any]) -> list[PromptSection]:
    summaries: list[PromptSection] = []
    for section in suite.get("sections", []):
        summaries.append(
            PromptSection(
                str(section["slug"]),
                str(section.get("title") or section["slug"]),
                len(section.get("prompts", [])),
            )
        )
    return summaries


def _load_prompt_items(source: str) -> list[PromptItem]:
    if source == BATCH_ALL_SOURCE:
        items: list[PromptItem] = []
        for file_name in BATCH_PROMPT_FILES:
            items.extend(_load_prompt_items(file_name))
        return items

    file_name, section = _split_prompt_source(source)
    prompts = _prompt_items_from_suite(file_name, _load_prompt_suite(file_name))
    if section is None:
        return prompts
    selected = [prompt for prompt in prompts if prompt.section == section]
    if not selected:
        raise HTTPException(status_code=400, detail="Unknown batch prompt section")
    return selected


def _batch_source_title(title: str, section_title: str | None = None) -> str:
    if section_title is None:
        return title
    return f"{title} - {section_title}"


def _run_batch_tasks(run_ids: list[str], store, settings) -> None:
    with BATCH_RUN_LOCK:
        for run_id in run_ids:
            run = store.get_run(run_id)
            if run is None or run.status != "idle" or run.stopRequested:
                continue
            run_agent(run_id, store, settings)


@router.get("", response_model=list[Run])
async def list_tasks(request: Request) -> list[Run]:
    # Tasks are the same persisted run records shown through a history-oriented route.
    return request.app.state.runs_store.list_runs()


@router.get("/batch-prompts", response_model=list[BatchPromptSource])
async def list_batch_prompt_sources() -> list[BatchPromptSource]:
    sources: list[BatchPromptSource] = []
    total = 0
    for file_name in BATCH_PROMPT_FILES:
        suite = _load_prompt_suite(file_name)
        title = _suite_title(file_name, suite)
        prompts = _prompt_items_from_suite(file_name, suite)
        total += len(prompts)
        sources.append(
            BatchPromptSource(id=file_name, title=_batch_source_title(title), count=len(prompts), file=file_name)
        )
        for section in _prompt_section_summaries(suite):
            sources.append(
                BatchPromptSource(
                    id=f"{file_name}#{section.slug}",
                    title=_batch_source_title(title, section.title),
                    count=section.count,
                    file=file_name,
                    section=section.slug,
                )
            )
    return [BatchPromptSource(id=BATCH_ALL_SOURCE, title="All prompt suites", count=total), *sources]


@router.post("/batch-tests", response_model=CreateBatchTasksResponse)
async def create_batch_tasks(
    payload: CreateBatchTasksRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> CreateBatchTasksResponse:
    prompt_items = _load_prompt_items(payload.source)
    offset = max(payload.offset, 0)
    limit = len(prompt_items) - offset if payload.all_remaining else max(payload.limit, 1)
    selected = prompt_items[offset : offset + limit]
    if not selected:
        raise HTTPException(status_code=400, detail="No prompts available for the requested range")

    store = request.app.state.runs_store
    settings = get_settings()
    run_ids: list[str] = []
    for prompt in selected:
        start_url = _start_url_for_task(prompt.task, "")
        run_id = f"run_{uuid4().hex[:18]}"
        run = Run(
            id=run_id,
            title=_title_for_task(prompt.task),
            task=prompt.task,
            url=start_url,
            status="idle",
            controlStatus="idle",
            inputs={
                "task": prompt.task,
                "url": start_url,
                "model": settings.model_name,
                "browser": settings.browser_channel,
                "batch_suite": payload.source,
                "batch_source": prompt.source,
                "batch_section": prompt.section,
                "batch_prompt_number": prompt.number,
                "batch_run_sequentially": payload.run_sequentially,
            },
            messages=[
                ChatMessage(
                    id=f"msg_{uuid4().hex[:10]}",
                    role="user",
                    content=prompt.task,
                    createdAt=_now(),
                )
            ],
        )
        store.create_run(run)
        run_ids.append(run_id)
    if payload.run_sequentially:
        background_tasks.add_task(_run_batch_tasks, run_ids, store, settings)
    return CreateBatchTasksResponse(run_ids=run_ids, count=len(run_ids), run_sequentially=payload.run_sequentially)


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(run_id: str, request: Request) -> Response:
    # Deleting a task removes only local history, not external artifacts already exported.
    deleted = request.app.state.runs_store.delete_run(run_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
