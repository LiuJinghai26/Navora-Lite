from app.agent.actions import AgentAction


# Simple result and error types keep runner failure handling explicit.
class PlannerResult:
    def __init__(self, actions: list[AgentAction], fallback_reason: str | None = None):
        self.actions = actions
        self.fallback_reason = fallback_reason


class PlannerConfigurationError(Exception):
    pass


class PlannerError(Exception):
    pass


class TaskRecognitionError(PlannerError):
    pass
