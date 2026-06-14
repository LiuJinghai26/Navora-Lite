from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["goto", "click", "fill", "press", "scroll", "wait", "extract", "finish", "ask_user"]
    target: str | None = None
    selector: str | None = None
    value: str | None = None
    url: str | None = None
    key: str | None = None
    direction: Literal["up", "down"] | None = None
    amount: int | None = None
    ms: int | None = None
    condition: str | None = None
    # Keep the public JSON key as "schema" while avoiding BaseModel.schema shadowing.
    extract_schema: dict[str, Any] | None = Field(default=None, alias="schema")
    result: Any | None = None
    message: str | None = None
    reason: str | None = None


def describe_action(action: AgentAction) -> str:
    if action.type == "goto":
        return f"Navigate to {action.url}"
    if action.type == "fill":
        return f"Fill {action.target or action.selector}"
    if action.type == "click":
        return f"Click {action.target or action.selector}"
    if action.type == "press":
        return f"Press {action.key}"
    if action.type == "scroll":
        return f"Scroll {action.direction}"
    if action.type == "wait":
        return action.condition or f"Wait {action.ms or 500}ms"
    if action.type == "extract":
        return f"Extract {action.target}" if action.target else "Extract information"
    if action.type == "finish":
        return "Finish run"
    return action.message or "Ask user"


def target_to_selector(target: str | None) -> str | None:
    if not target:
        return None
    key = target.lower()
    mapping = {
        "search input": "#search-input",
        "search field": "#search-input",
        "search box": "#search-input",
        "search button": "#search-button",
        "product aurora task lamp": "[data-testid='product-link']",
        "aurora task lamp": "[data-testid='product-link']",
        "product link": "[data-testid='product-link']",
        "open product": "[data-testid='product-link']",
        "color warm white": "#color-warm-white",
        "warm white": "#color-warm-white",
        "quantity": "#quantity",
        "quantity input": "#quantity",
        "add to cart": "#add-to-cart",
        "cart": "#cart-link",
        "cart button": "#cart-link",
        "cart link": "#cart-link",
    }
    return mapping.get(key)
