from pathlib import Path

from fastapi import APIRouter

from app.config import get_settings
from app.models import SettingsPayload

router = APIRouter(prefix="/api/settings", tags=["settings"])

SETTINGS_KEYS = [
    "MODEL_PROVIDER",
    "MODEL_NAME",
    "API_BASE",
    "API_KEY",
    "MAX_TOKENS",
    "TEMPERATURE",
    "BROWSER_HEADLESS",
]


def _env_path() -> Path:
    return Path(".env")


def _serialize(payload: SettingsPayload) -> dict[str, str]:
    values = {
        "MODEL_PROVIDER": payload.MODEL_PROVIDER,
        "MODEL_NAME": payload.MODEL_NAME,
        "API_BASE": payload.API_BASE,
        "MAX_TOKENS": str(payload.MAX_TOKENS),
        "TEMPERATURE": str(payload.TEMPERATURE),
        "BROWSER_HEADLESS": str(payload.BROWSER_HEADLESS).lower(),
    }
    if payload.API_KEY != "********":
        values["API_KEY"] = payload.API_KEY
    return values


def _write_env(updates: dict[str, str]) -> None:
    path = _env_path()
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen: set[str] = set()
    next_lines: list[str] = []

    for line in lines:
        key, separator, _ = line.partition("=")
        if separator and key in updates:
            next_lines.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            next_lines.append(line)

    for key in SETTINGS_KEYS:
        if key in updates and key not in seen:
            next_lines.append(f"{key}={updates[key]}")

    path.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")


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
    _write_env(_serialize(payload))
    get_settings.cache_clear()
    return await get_model_settings()
