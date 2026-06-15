import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from app.agent.actions import AgentAction
from app.agent.runner import OPEN_BROWSER_SESSIONS, _updated_extraction_payload, close_or_keep_browser_session, run_agent
from app.llm.schemas import PlannerResult
from app.models import ChatMessage, Run
from app.storage.runs_store import RunsStore


def test_runner_marks_planner_fallback_as_failure(monkeypatch, tmp_path):
    # Planner fallback reasons are surfaced as planning failures in the run timeline.
    async def fake_plan_actions(*args, **kwargs):
        return PlannerResult(
            [AgentAction(type="goto", url="http://localhost:8000/mock/findparts")],
            fallback_reason="Model planner failed",
        )

    store = RunsStore(tmp_path / "runs.json")
    store.create_run(
        Run(
            id="run_test",
            title="Test Run",
            task="Open Wikipedia",
            url="https://www.wikipedia.org/",
            messages=[
                ChatMessage(
                    id="msg_test",
                    role="user",
                    content="Open Wikipedia",
                    createdAt=datetime.now(timezone.utc).isoformat(),
                )
            ],
        )
    )
    monkeypatch.setattr("app.agent.runner.plan_actions", fake_plan_actions)

    run_agent("run_test", store, SimpleNamespace())

    run = store.get_run("run_test")
    assert run is not None
    assert run.status == "failed"
    assert run.failureType == "planning_failed"
    assert all(step.action != "fallback" for step in run.timeline)


def test_headless_browser_session_closes_after_run():
    class FakeSession:
        def __init__(self):
            self.closed = False
            self.kept_open = False

        async def close(self):
            self.closed = True

        async def keep_open(self):
            self.kept_open = True

    session = FakeSession()
    asyncio.run(close_or_keep_browser_session(session, SimpleNamespace(browser_headless=True)))

    assert session.closed is True
    assert session.kept_open is False


def test_visible_browser_session_stays_open_after_run():
    class FakeSession:
        def __init__(self):
            self.closed = False
            self.kept_open = False

        async def close(self):
            self.closed = True

        async def keep_open(self):
            self.kept_open = True

    session = FakeSession()
    OPEN_BROWSER_SESSIONS.clear()
    try:
        asyncio.run(close_or_keep_browser_session(session, SimpleNamespace(browser_headless=False)))

        assert session.closed is False
        assert session.kept_open is True
        assert session in OPEN_BROWSER_SESSIONS
    finally:
        OPEN_BROWSER_SESSIONS.clear()


def test_multiple_extractions_are_accumulated():
    first = {"title": "First page"}
    second = {"title": "Linked page"}

    current = _updated_extraction_payload(None, AgentAction(type="extract", target="First page facts"), first)
    combined = _updated_extraction_payload(current, AgentAction(type="extract", target="Linked page facts"), second)

    assert current == first
    assert combined["latest"] == second
    assert combined["extracts"] == [
        {"target": "Previous extract", "data": first},
        {"target": "Linked page facts", "data": second},
    ]
