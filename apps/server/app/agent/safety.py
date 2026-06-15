from app.agent.actions import AgentAction


# Conservative keyword guard for browser actions before they reach Playwright.
RISKY_TERMS = [
    "pay",
    "payment",
    "checkout",
    "add to cart",
    "submit order",
    "place order",
    "delete account",
    "change password",
    "modify password",
    "send sensitive",
    "upload private",
    "captcha",
    "2fa",
    "credit card",
    "password",
    "提交订单",
    "支付",
    "加入购物车",
    "删除账号",
    "修改密码",
    "验证码",
]

DISALLOWED_MOCK_TERMS = [
    "aurora task lamp",
    "mock/findparts",
    "localhost:8000/mock",
    "127.0.0.1:8000/mock",
]


def is_high_risk_action(action: AgentAction) -> bool:
    # Flatten planner-controlled fields so selectors, URLs, and messages are checked uniformly.
    text = " ".join(
        str(value).lower()
        for value in [action.type, action.target, action.selector, action.value, action.url, action.reason, action.message]
        if value
    )
    return any(term in text for term in RISKY_TERMS)


def assert_safe_action(action: AgentAction) -> None:
    # Keep the old local shopping demo disabled even if a model tries to revive it.
    text = " ".join(
        str(value).lower()
        for value in [action.type, action.target, action.selector, action.value, action.url, action.reason, action.message]
        if value
    )
    if any(term in text for term in DISALLOWED_MOCK_TERMS):
        raise ValueError("Local mock shopping flow is disabled.")
    if is_high_risk_action(action):
        raise ValueError("This step requires user confirmation.")
