from app.agent.actions import AgentAction


class PlannerResult:
    def __init__(self, actions: list[AgentAction], fallback_reason: str | None = None):
        self.actions = actions
        self.fallback_reason = fallback_reason

