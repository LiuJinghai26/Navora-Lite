from app.agent.actions import AgentAction


# Presets provide model-free browser demos from the Tasks page.
PRESET_TASKS = {
    "hn-top-story": {
        "title": "Hacker News Top Story",
        "start_url": "https://news.ycombinator.com/",
        "actions": [
            AgentAction(type="goto", url="https://news.ycombinator.com/"),
            AgentAction(type="wait", ms=1000, condition="Wait for Hacker News stories"),
            AgentAction(type="extract", target="hacker news top story"),
        ],
    },
    "wikipedia-python-summary": {
        "title": "Wikipedia Python Summary",
        "start_url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "actions": [
            AgentAction(type="goto", url="https://en.wikipedia.org/wiki/Python_(programming_language)"),
            AgentAction(type="wait", ms=1000, condition="Wait for the Wikipedia article"),
            AgentAction(type="extract", target="wikipedia python summary"),
        ],
    },
    "mdn-api-research": {
        "title": "MDN Web API Research",
        "start_url": "https://developer.mozilla.org/en-US/docs/Web/API",
        "actions": [
            AgentAction(type="goto", url="https://developer.mozilla.org/en-US/docs/Web/API"),
            AgentAction(type="wait", ms=1000, condition="Wait for the MDN Web API index"),
            AgentAction(type="extract", target="mdn web api overview"),
            AgentAction(type="goto", url="https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API"),
            AgentAction(type="wait", ms=1000, condition="Wait for the Fetch API page"),
            AgentAction(type="extract", target="mdn fetch api detail"),
        ],
    },
}


def preset_plan(preset_id: str | None) -> list[AgentAction] | None:
    if not preset_id:
        return None
    preset = PRESET_TASKS.get(preset_id)
    if not preset:
        return None
    # Return copies so a run cannot mutate shared preset action objects.
    return [action.model_copy(deep=True) for action in preset["actions"]]
