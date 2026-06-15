from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import events, runs, settings as settings_api, tasks
from app.config import get_settings
from app.storage.runs_store import RunsStore


settings = get_settings()
app = FastAPI(title="Navora Lite API", version="0.1.0")
# The frontend runs on a separate port during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
# Screenshots are saved on disk and served directly to the web app.
app.mount("/artifacts", StaticFiles(directory=str(settings.artifacts_dir)), name="artifacts")
app.state.runs_store = RunsStore(settings.run_storage_path)

app.include_router(runs.router)
app.include_router(tasks.router)
app.include_router(events.router)
app.include_router(settings_api.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "navora-lite"}
