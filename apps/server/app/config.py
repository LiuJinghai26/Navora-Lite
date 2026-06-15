from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Pydantic reads .env from the backend working directory.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Navora Lite"
    public_base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_provider: str = "openai-compatible"
    model_name: str = "qwen3-32b"
    api_base: str = ""
    api_key: str = ""
    max_tokens: int = 4096
    temperature: float = 0.2
    llm_timeout_seconds: float = 60.0

    browser_headless: bool = True
    browser_channel: str = "chromium"
    browser_viewport_width: int = 1280
    browser_viewport_height: int = 800

    run_storage_path: Path = Path("./data/runs.json")
    artifacts_dir: Path = Path("./data/artifacts")
    runner_step_delay_seconds: float = 0.25

    @property
    def cors_origin_list(self) -> list[str]:
        # FastAPI expects a list, while .env keeps origins as a comma-separated string.
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    # Cache settings for normal requests; settings API clears this after writing .env.
    return Settings()
