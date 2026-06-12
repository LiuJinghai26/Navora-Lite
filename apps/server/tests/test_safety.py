import pytest

from app.agent.actions import AgentAction
from app.agent.safety import assert_safe_action


def test_safety_blocks_high_risk_actions():
    with pytest.raises(ValueError):
        assert_safe_action(AgentAction(type="click", target="submit order"))


def test_safety_allows_demo_cart_action():
    assert_safe_action(AgentAction(type="click", target="add to cart"))

