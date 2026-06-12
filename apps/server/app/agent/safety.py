from app.agent.actions import AgentAction


RISKY_TERMS = [
    "pay",
    "payment",
    "checkout",
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
    "删除账号",
    "修改密码",
    "验证码",
]


def is_high_risk_action(action: AgentAction) -> bool:
    text = " ".join(
        str(value).lower()
        for value in [action.type, action.target, action.selector, action.value, action.url, action.reason, action.message]
        if value
    )
    return any(term in text for term in RISKY_TERMS)


def assert_safe_action(action: AgentAction) -> None:
    if is_high_risk_action(action):
        raise ValueError("This step requires user confirmation.")

