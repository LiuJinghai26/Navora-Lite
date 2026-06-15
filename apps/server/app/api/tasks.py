from fastapi import APIRouter, HTTPException, Request, Response, status

from app.models import Run

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[Run])
async def list_tasks(request: Request) -> list[Run]:
    # Tasks are the same persisted run records shown through a history-oriented route.
    return request.app.state.runs_store.list_runs()


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(run_id: str, request: Request) -> Response:
    # Deleting a task removes only local history, not external artifacts already exported.
    deleted = request.app.state.runs_store.delete_run(run_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
