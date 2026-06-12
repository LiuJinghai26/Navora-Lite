from fastapi import APIRouter

from app.config import get_settings
from app.models import SettingsPayload

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsPayload)
async def get_model_settings() -> SettingsPayload:
    settings = get_settings()
    return SettingsPayload(
        MODEL_PROVIDER=settings.model_provider,
        MODEL_NAME=settings.model_name,
        API_BASE=settings.api_base,
        API_KEY="" if not settings.api_key else "********",
        MAX_TOKENS=settings.max_tokens,
        TEMPERATURE=settings.temperature,
        BROWSER_HEADLESS=settings.browser_headless,
    )


@router.post("", response_model=SettingsPayload)
async def save_model_settings(payload: SettingsPayload) -> SettingsPayload:
    return payload

