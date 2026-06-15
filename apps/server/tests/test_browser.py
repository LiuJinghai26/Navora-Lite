import asyncio
from types import SimpleNamespace

import pytest

from app.agent.browser import PlaywrightBrowserSession


def test_click_requires_selector_or_role_fallback():
    session = PlaywrightBrowserSession(None, None, SimpleNamespace())

    with pytest.raises(ValueError, match="No click selector candidates"):
        asyncio.run(session._try_click([None]))


def test_fill_requires_selector_candidate():
    session = PlaywrightBrowserSession(None, None, SimpleNamespace())

    with pytest.raises(ValueError, match="No fill selector candidates"):
        asyncio.run(session._try_fill([None], "value"))
