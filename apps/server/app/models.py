from typing import Any, Literal

from pydantic import BaseModel, Field


RunStatus = Literal["idle", "running", "completed", "failed", "stopped"]
StepStatus = Literal["pending", "running", "success", "failed", "skipped", "stopped"]
ChatRole = Literal["user", "assistant", "system"]
FailureType = Literal["recognition_failed", "planning_failed", "execution_failed"]


class ChecklistItem(BaseModel):
    text: str
    status: Literal["pending", "running", "success", "failed"] = "pending"
    time: str | None = None


class ChatMessage(BaseModel):
    id: str
    role: ChatRole
    content: str
    createdAt: str
    checklist: list[ChecklistItem] = Field(default_factory=list)


class TimelineStep(BaseModel):
    id: str
    index: int
    action: str
    description: str
    status: StepStatus
    startedAt: str | None = None
    endedAt: str | None = None
    durationMs: int | None = None
    screenshotUrl: str | None = None
    error: str | None = None


class ScreenshotItem(BaseModel):
    id: str
    title: str
    imageUrl: str
    createdAt: str


class Run(BaseModel):
    id: str
    title: str
    task: str
    url: str
    status: RunStatus = "idle"
    controlStatus: Literal["idle", "controlling", "stopped", "completed", "failed"] = "idle"
    startedAt: str | None = None
    finishedAt: str | None = None
    durationMs: int | None = None
    messages: list[ChatMessage] = Field(default_factory=list)
    timeline: list[TimelineStep] = Field(default_factory=list)
    screenshots: list[ScreenshotItem] = Field(default_factory=list)
    extracted: Any | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    fallbackReason: str | None = None
    failureType: FailureType | None = None
    stopRequested: bool = False


class CreateRunRequest(BaseModel):
    task: str
    url: str = ""
    auto_start: bool = True
    preset_id: str | None = None


class CreateRunResponse(BaseModel):
    run_id: str
    status: RunStatus


class SettingsPayload(BaseModel):
    MODEL_PROVIDER: str = "openai-compatible"
    MODEL_NAME: str = "qwen3-32b"
    API_BASE: str = ""
    API_KEY: str = ""
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.2
    BROWSER_HEADLESS: bool = True


class RunEvent(BaseModel):
    type: str
    message: ChatMessage | None = None
    step: TimelineStep | None = None
    image_url: str | None = None
    status: RunStatus | None = None
    data: Any | None = None
    error: str | None = None
    run: Run | None = None
