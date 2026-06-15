import asyncio
from types import SimpleNamespace

import pytest

from app.agent.actions import AgentAction
from app.agent.browser import PlaywrightBrowserSession, _requested_fields


def test_click_requires_selector_or_role_fallback():
    session = PlaywrightBrowserSession(None, None, SimpleNamespace())

    with pytest.raises(ValueError, match="No click selector candidates"):
        asyncio.run(session._try_click([None]))


def test_fill_requires_selector_candidate():
    session = PlaywrightBrowserSession(None, None, SimpleNamespace())

    with pytest.raises(ValueError, match="No fill selector candidates"):
        asyncio.run(session._try_fill([None], "value"))


def test_requested_fields_collects_extract_schema_keys():
    action = AgentAction(
        type="extract",
        target="Product facts",
        extract_schema={"name": "string", "price": "string", "details": {"rating": "string"}},
    )

    assert _requested_fields(action) == ["name", "price", "details", "rating"]
