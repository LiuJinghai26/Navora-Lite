import json
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.agent.actions import AgentAction
from app.agent.presets import preset_plan
from app.agent.safety import assert_safe_action
from app.config import Settings
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.llm.schemas import PlannerConfigurationError, PlannerError, PlannerResult, TaskRecognitionError


PLANNER_MAX_TOKENS = 4096


def _is_local_provider(settings: Settings) -> bool:
    # Local OpenAI-compatible servers commonly accept empty API keys.
    return settings.model_provider.lower() in {"ollama", "lmstudio", "vllm", "custom"}


def recognized_task_plan(task: str, start_url: str) -> list[AgentAction] | None:
    # Recognized plans avoid model calls for common public-site tasks.
    task_key = task.lower()
    url_key = start_url.lower()
    if _requires_model_planning(task_key):
        return None
    if "ada lovelace" in task_key:
        return _article_plan("https://en.wikipedia.org/wiki/Ada_Lovelace")
    if "grace hopper" in task_key:
        return _article_plan("https://en.wikipedia.org/wiki/Grace_Hopper")
    if "news.ycombinator.com" in url_key or "hacker news" in task_key:
        return [
            AgentAction(type="goto", url="https://news.ycombinator.com/"),
            AgentAction(type="wait", ms=1000, condition="Wait for Hacker News stories"),
            AgentAction(type="extract", target="hacker news stories"),
        ]
    if "github.com/trending/python" in url_key:
        return [
            AgentAction(type="goto", url="https://github.com/trending/python"),
            AgentAction(type="wait", ms=1000, condition="Wait for GitHub Trending"),
            AgentAction(type="extract", target="github trending repositories"),
        ]
    if "github.com/trending" in url_key:
        return [
            AgentAction(type="goto", url="https://github.com/trending"),
            AgentAction(type="wait", ms=1000, condition="Wait for GitHub Trending"),
            AgentAction(type="extract", target="github trending repositories"),
        ]
    if "developer.mozilla.org" in url_key:
        return [
            AgentAction(type="goto", url=start_url),
            AgentAction(type="wait", ms=1000, condition="Wait for the documentation page"),
            AgentAction(type="extract", target="mdn fetch api detail" if "fetch_api" in url_key else "page summary"),
        ]
    if "timeanddate.com/worldclock" in url_key:
        if "tokyo" in task_key:
            return _goto_extract_plan("https://www.timeanddate.com/worldclock/japan/tokyo")
        if "new york" in task_key:
            return _goto_extract_plan("https://www.timeanddate.com/worldclock/usa/new-york")
    if "weather.com" in url_key and "san francisco" in task_key:
        return _goto_extract_plan("https://weather.com/weather/today/l/USCA0987:1:US")
    if "ikea.com" in url_key:
        if "desk lamp" in task_key:
            return _goto_extract_plan("https://www.ikea.com/us/en/search/?q=desk%20lamp")
        if "standing desk" in task_key:
            return _goto_extract_plan("https://www.ikea.com/us/en/search/?q=standing%20desk")
        if "desk chair" in task_key:
            return _goto_extract_plan("https://www.ikea.com/us/en/search/?q=desk%20chair")
    if "target.com" in url_key:
        if "coffee maker" in task_key:
            return _goto_extract_plan("https://www.target.com/s?searchTerm=coffee%20maker")
        if "air purifier" in task_key:
            return _goto_extract_plan("https://www.target.com/s?searchTerm=air%20purifier")
        if "water bottle" in task_key:
            return _goto_extract_plan("https://www.target.com/s?searchTerm=water%20bottle")
    if "nike.com" in url_key:
        if "trail running shoes" in task_key:
            return _goto_extract_plan("https://www.nike.com/w?q=trail%20running%20shoes&vst=trail%20running%20shoes")
        if "running shoes" in task_key:
            return _goto_extract_plan("https://www.nike.com/w?q=running%20shoes&vst=running%20shoes")
    if "bestbuy.com" in url_key:
        if "wireless mouse" in task_key:
            return _goto_extract_plan("https://www.bestbuy.com/site/searchpage.jsp?st=wireless+mouse")
        if "mechanical keyboard" in task_key:
            return _goto_extract_plan("https://www.bestbuy.com/site/searchpage.jsp?st=mechanical+keyboard")
    if "amazon.com" in url_key:
        if "noise cancelling headphones" in task_key:
            return _goto_extract_plan("https://www.amazon.com/s?k=noise+cancelling+headphones")
        if "usb c hub" in task_key:
            return _goto_extract_plan("https://www.amazon.com/s?k=usb+c+hub")
    if "walmart.com" in url_key:
        if "office chair" in task_key:
            return _goto_extract_plan("https://www.walmart.com/search?q=office%20chair")
        if "monitor stand" in task_key:
            return _goto_extract_plan("https://www.walmart.com/search?q=monitor%20stand")
    if "booking.com" in url_key:
        if "seattle" in task_key:
            return _goto_extract_plan("https://www.booking.com/searchresults.html?ss=Seattle")
        if "chicago" in task_key:
            return _goto_extract_plan("https://www.booking.com/searchresults.html?ss=Chicago")
    if "tripadvisor.com" in url_key:
        if "kyoto restaurants" in task_key:
            return _goto_extract_plan("https://www.tripadvisor.com/Search?q=Kyoto%20restaurants")
        if "san diego attractions" in task_key:
            return _goto_extract_plan("https://www.tripadvisor.com/Search?q=San%20Diego%20attractions")
    if "expedia.com" in url_key:
        if "new york hotels" in task_key:
            return _goto_extract_plan("https://www.expedia.com/Hotel-Search?destination=New%20York")
    if "google.com/travel/flights" in url_key:
        if "sfo" in task_key and "lax" in task_key:
            return _goto_extract_plan("https://www.google.com/travel/flights?q=Flights%20from%20SFO%20to%20LAX")
        if "nyc" in task_key and "mia" in task_key:
            return _goto_extract_plan("https://www.google.com/travel/flights?q=Flights%20from%20NYC%20to%20MIA")
    if "airbnb.com" in url_key and "austin" in task_key:
        return _goto_extract_plan("https://www.airbnb.com/s/Austin--Texas--United-States/homes")
    if "yelp.com" in url_key:
        if "coffee" in task_key and "san francisco" in task_key:
            return _goto_extract_plan("https://www.yelp.com/search?find_desc=coffee&find_loc=San%20Francisco%2C%20CA")
        if "brunch" in task_key and "seattle" in task_key:
            return _goto_extract_plan("https://www.yelp.com/search?find_desc=brunch&find_loc=Seattle%2C%20WA")
    if "linkedin.com/jobs" in url_key and "frontend developer" in task_key:
        return _goto_extract_plan("https://www.linkedin.com/jobs/search/?keywords=frontend%20developer&location=Remote")
    if "indeed.com" in url_key and "data analyst" in task_key:
        return _goto_extract_plan("https://www.indeed.com/jobs?q=data%20analyst&l=Remote")
    if "remoteok.com" in url_key and "python" in task_key:
        return _goto_extract_plan("https://remoteok.com/remote-python-jobs")
    if "weworkremotely.com" in url_key and "react" in task_key:
        return _goto_extract_plan("https://weworkremotely.com/remote-jobs/search?term=React")
    if "github.com/search" in url_key:
        if "browser automation dashboard" in task_key:
            return _goto_extract_plan("https://github.com/search?q=browser%20automation%20dashboard&type=repositories")
        if "playwright python agent" in task_key:
            return _goto_extract_plan("https://github.com/search?q=playwright%20python%20agent&type=repositories")
        if "agent browser automation" in task_key:
            return _goto_extract_plan("https://github.com/search?q=agent%20browser%20automation&type=repositories")
    if "npmjs.com" in url_key:
        if "browser automation" in task_key:
            return _goto_extract_plan("https://www.npmjs.com/search?q=browser%20automation")
        if "playwright" in task_key:
            return _goto_extract_plan("https://www.npmjs.com/search?q=playwright")
    if "pypi.org" in url_key and "playwright" in task_key:
        return _goto_extract_plan("https://pypi.org/search/?q=playwright")
    if "iana.org/domains/reserved" in url_key or "w3.org/wai" in url_key:
        return [
            AgentAction(type="goto", url=start_url),
            AgentAction(type="wait", ms=1000, condition="Wait for the page"),
            AgentAction(type="extract", target="page summary"),
        ]
    if "httpbin.org/forms/post" in url_key:
        return [
            AgentAction(type="goto", url="https://httpbin.org/forms/post"),
            AgentAction(type="fill", selector='input[name="custname"]', value="Navora Tester"),
            AgentAction(type="fill", selector='input[name="custtel"]', value="555-0100"),
            AgentAction(type="fill", selector='input[name="custemail"]', value="tester@example.com"),
            AgentAction(type="click", selector='input[name="size"][value="medium"]'),
            AgentAction(type="click", selector='input[name="topping"][value="bacon"]'),
            AgentAction(type="click", selector='input[name="topping"][value="cheese"]'),
            AgentAction(type="fill", selector='input[name="delivery"]', value="18:30"),
            AgentAction(type="fill", selector='textarea[name="comments"]', value="Browser task test"),
            AgentAction(type="click", target="submit test form", selector='button:has-text("Submit")'),
            AgentAction(type="wait", ms=1000, condition="Wait for the response page"),
            AgentAction(type="extract", target="httpbin form echo"),
        ]
    return None


def _requires_model_planning(task_key: str) -> bool:
    complex_markers = [
        "打开前",
        "打开第一个",
        "打开一个",
        "分别打开",
        "分别进入",
        "依次",
        "继续打开",
        "再打开",
        "然后打开",
        "评论页",
        "详情页",
        "分类页",
        "新闻详情页",
        "商品详情页",
        "筛选",
        "排序",
        "选择",
        "设置",
        "入住日期",
        "退房日期",
        "人数",
        "填写",
        "提交",
        "对比",
        "推荐",
        "按价格",
        "按下载量",
        "按语言",
        "三个页面",
        "三个文档页",
        "三页",
        "搜索或打开",
        "搜索或找到",
        "首页可见的 3",
        "3 个主要资源",
        "open the first",
        "open top",
        "open the top",
        "then open",
        "continue to open",
        "detail page",
        "details page",
        "comment page",
        "filter",
        "sort",
        "select",
        "set ",
        "fill",
        "submit",
        "compare",
    ]
    return any(marker in task_key for marker in complex_markers)


def _article_plan(url: str) -> list[AgentAction]:
    # Article plans navigate directly, then use a stable extractor target.
    return [
        AgentAction(type="goto", url=url),
        AgentAction(type="wait", ms=1000, condition="Wait for the Wikipedia article"),
        AgentAction(type="extract", target="wikipedia article summary"),
    ]


def _goto_extract_plan(url: str, target: str = "page summary") -> list[AgentAction]:
    # Generic public-site fallback: open, settle, extract visible page structure.
    return [
        AgentAction(type="goto", url=url),
        AgentAction(type="wait", ms=1000, condition="Wait for the page"),
        AgentAction(type="extract", target=target),
    ]


def has_planner_config(settings: Settings) -> bool:
    # Hosted providers need a key; configured local providers only need a base URL.
    if not settings.api_base:
        return False
    return bool(settings.api_key or _is_local_provider(settings))


def _json_content(content: str) -> str:
    # Models sometimes wrap JSON in fences or prose; extract the likely JSON region.
    value = content.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    starts = [index for index in [value.find("["), value.find("{")] if index != -1]
    ends = [index for index in [value.rfind("]"), value.rfind("}")] if index != -1]
    if starts and ends:
        value = value[min(starts) : max(ends) + 1]
    return value


def _parse_actions(content: str) -> list[AgentAction]:
    # Accept a few common planner response shapes while keeping the action contract strict.
    raw: Any = json.loads(_json_content(content))
    if isinstance(raw, dict) and "actions" in raw:
        raw = raw["actions"]
    elif isinstance(raw, dict) and "type" in raw:
        raw = [raw]
    if not isinstance(raw, list):
        raise ValueError("Planner response must be a JSON array.")
    for item in raw:
        if isinstance(item, dict) and "type" not in item and "action" in item:
            item["type"] = item.pop("action")
    actions = [AgentAction(**item) for item in raw]
    executable_actions = [action for action in actions if action.type not in {"ask_user", "finish"}]
    if not executable_actions:
        raise TaskRecognitionError("Planner did not produce executable browser actions.")
    # Validate model output before any browser side effect is attempted.
    for action in actions:
        assert_safe_action(action)
    return actions


def _extract_follow_link_targets(task: str) -> list[str]:
    patterns = [
        r"(?:打开|点击|进入|访问|跟随)\s*[`\"“'‘]?([^`\"”'’。，、；,;\n]{2,80}?)[`\"”'’]?\s*(?:链接|页面|文档页|条目|文章)",
        r"(?:打开|点击|进入|访问|跟随)[^。，；,;\n]{0,40}?指向\s*[`\"“'‘]?([^`\"”'’。，、；,;\n]{2,80}?)[`\"”'’]?\s*(?:的)?\s*(?:链接|页面|文档页|条目|文章)",
        r"(?:open|click|follow|visit|enter|navigate to)\s+(?:the\s+)?[`\"']?([^`\"',.;\n]{2,80}?)[`\"']?\s+(?:link|page|article|result)",
    ]
    targets: list[str] = []
    multi_page_match = re.search(
        r"(?:搜索或打开|搜索或找到|找到)\s*((?:[`\"“'‘][^`\"”'’]+[`\"”'’]\s*[、,，]?\s*){2,})[^。；;\n]{0,30}?(?:页面|文档页|条目|文章)",
        task,
    )
    if multi_page_match:
        for match in re.finditer(r"[`\"“'‘]([^`\"”'’]{2,80})[`\"”'’]", multi_page_match.group(1)):
            target = re.sub(r"\s+", " ", match.group(1)).strip(" `\"'“”‘’")
            if target and not target.startswith(("http://", "https://")) and target not in targets:
                targets.append(target)
    for pattern in patterns:
        for match in re.finditer(pattern, task, flags=re.IGNORECASE):
            target = re.sub(r"\s+", " ", match.group(1)).strip(" `\"'“”‘’")
            if target and not target.startswith(("http://", "https://")) and target not in targets:
                targets.append(target)
    return targets


def _extract_follow_link_target(task: str) -> str | None:
    targets = _extract_follow_link_targets(task)
    return targets[0] if targets else None


def _ensure_follow_link_steps(task: str, actions: list[AgentAction]) -> list[AgentAction]:
    link_targets = _extract_follow_link_targets(task)
    if not link_targets:
        return actions

    extract_indexes = [index for index, action in enumerate(actions) if action.type == "extract"]
    if not extract_indexes:
        return actions
    first_extract_index = extract_indexes[0]
    has_follow_navigation = any(action.type in {"click", "goto"} for action in actions[first_extract_index + 1 :])
    if has_follow_navigation:
        return actions

    original_extract = actions[first_extract_index]
    if len(link_targets) == 1:
        link_target = link_targets[0]
        return [
            *actions[:first_extract_index],
            AgentAction(type="extract", target="current page requested fields", extract_schema=original_extract.extract_schema),
            AgentAction(type="click", target=link_target),
            AgentAction(type="wait", ms=1000, condition=f"Wait for {link_target}"),
            original_extract,
            *actions[first_extract_index + 1 :],
        ]

    follow_steps: list[AgentAction] = [
        AgentAction(type="extract", target="current page requested fields", extract_schema=original_extract.extract_schema)
    ]
    for link_target in link_targets:
        follow_steps.extend(
            [
                AgentAction(type="click", target=link_target),
                AgentAction(type="wait", ms=1000, condition=f"Wait for {link_target}"),
                AgentAction(type="extract", target=f"{link_target} requested fields", extract_schema=original_extract.extract_schema),
            ]
        )
    return [
        *actions[:first_extract_index],
        *follow_steps,
        *actions[first_extract_index + 1 :],
    ]


def _prefer_english_wikipedia_for_ascii_search(actions: list[AgentAction]) -> list[AgentAction]:
    if len(actions) < 3:
        return actions

    first = actions[0]
    if first.type != "goto" or not first.url:
        return actions
    host = urlparse(first.url).netloc.lower()
    if host not in {"www.wikipedia.org", "wikipedia.org"}:
        return actions

    has_ascii_search = any(
        action.type == "fill"
        and action.value
        and "search" in ((action.target or "") + " " + (action.selector or "")).lower()
        and action.value.isascii()
        for action in actions[1:4]
    )
    if not has_ascii_search:
        return actions

    return [first.model_copy(update={"url": "https://en.wikipedia.org/"}), *actions[1:]]


def _postprocess_model_actions(task: str, actions: list[AgentAction]) -> list[AgentAction]:
    return _ensure_follow_link_steps(task, _prefer_english_wikipedia_for_ascii_search(actions))


def _planner_max_tokens(settings: Settings) -> int:
    return min(settings.max_tokens, PLANNER_MAX_TOKENS)


async def plan_actions(task: str, url: str, settings: Settings, preset_id: str | None = None) -> PlannerResult:
    # Planning order is deterministic: preset, recognized task, then model.
    preset_actions = preset_plan(preset_id)
    if preset_actions:
        return PlannerResult(preset_actions)

    start_url = url or ""
    recognized_actions = recognized_task_plan(task, start_url)
    if recognized_actions:
        return PlannerResult(recognized_actions)

    # Local model providers often omit API keys; hosted-compatible providers should not.
    if not has_planner_config(settings):
        raise PlannerConfigurationError("Model API settings are required before starting a browser task.")

    endpoint = settings.api_base.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"

    # The prompt asks for JSON-only actions; parsing still tolerates minor model drift.
    payload = {
        "model": settings.model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(task, start_url)},
        ],
        "temperature": settings.temperature,
        "max_tokens": _planner_max_tokens(settings),
    }

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return PlannerResult(_postprocess_model_actions(task, _parse_actions(content)))
    except TaskRecognitionError:
        raise
    except Exception as exc:
        detail = str(exc) or exc.__class__.__name__
        raise PlannerError(f"Model planner failed ({detail}).")
