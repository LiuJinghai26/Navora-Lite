import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/runs", tags=["events"])


def _event_payload(event) -> str:
    if hasattr(event, "model_dump"):
        data = event.model_dump(mode="json", exclude_none=True)
    else:
        data = event.dict(exclude_none=True)
    return f"data: {json.dumps(data)}\n\n"


@router.get("/{run_id}/events")
async def run_events(run_id: str, request: Request) -> StreamingResponse:
    store = request.app.state.runs_store
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    async def stream():
        # Send a full snapshot first so clients can reconnect without replaying old events.
        yield f"data: {json.dumps({'type': 'snapshot', 'run': run.model_dump(mode='json') if hasattr(run, 'model_dump') else run.dict()})}\n\n"
        async for queue in store.subscribe(run_id):
            while True:
                if await request.is_disconnected():
                    return
                event = await queue.get()
                yield _event_payload(event)

    return StreamingResponse(stream(), media_type="text/event-stream")
