import json
from typing import Any

import httpx

from app.agent.actions import AgentAction
from app.agent.presets import preset_plan
from app.agent.safety import assert_safe_action
from app.config import Settings
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.llm.schemas import PlannerResult


DEMO_PRODUCT = "AURORA TASK LAMP"
DEMO_COLOR = "Warm White"
DEMO_QUANTITY = "2"


def mock_plan(start_url: str = "http://localhost:8000/mock/findparts") -> list[AgentAction]:
    """Return the stable demo path used when no reliable model planner is available."""

    return [
        AgentAction(type="goto", url=start_url),
        AgentAction(type="fill", target="search input", value=DEMO_PRODUCT),
        AgentAction(type="click", target="search button"),
        AgentAction(type="click", target=f"product {DEMO_PRODUCT}"),
        AgentAction(type="click", target=f"color {DEMO_COLOR}"),
        AgentAction(type="fill", target="quantity", value=DEMO_QUANTITY),
        AgentAction(type="click", target="add to cart"),
        AgentAction(type="click", target="cart"),
        AgentAction(type="extract", schema={"product_name": "string", "color": "string", "quantity": "number", "subtotal": "string"}),
    ]


def _is_local_provider(settings: Settings) -> bool:
    return settings.model_provider.lower() in {"ollama", "lmstudio", "vllm", "custom"}


def _parse_actions(content: str) -> list[AgentAction]:
    raw: Any = json.loads(content)
    if isinstance(raw, dict) and "actions" in raw:
        raw = raw["actions"]
    if not isinstance(raw, list):
        raise ValueError("Planner response must be a JSON array.")
    actions = [AgentAction(**item) for item in raw]
    # Validate model output before any browser side effect is attempted.
    for action in actions:
        assert_safe_action(action)
    return actions


async def plan_actions(task: str, url: str, settings: Settings, preset_id: str | None = None) -> PlannerResult:
    preset_actions = preset_plan(preset_id)
    if preset_actions:
        return PlannerResult(preset_actions)

    start_url = url or "http://localhost:8000/mock/findparts"
    # Local model providers often omit API keys; hosted-compatible providers should not.
    if not settings.api_base:
        return PlannerResult(mock_plan(start_url), "No API_BASE configured; using mock planner.")
    if not settings.api_key and not _is_local_provider(settings):
        return PlannerResult(mock_plan(start_url), "No API_KEY configured; using mock planner.")

    endpoint = settings.api_base.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"

    payload = {
        "model": settings.model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(task, start_url)},
        ],
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return PlannerResult(_parse_actions(content))
    except Exception as exc:
        return PlannerResult(mock_plan(start_url), f"Model planner failed ({exc}); using mock planner.")
