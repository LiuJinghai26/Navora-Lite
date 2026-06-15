import pytest

from app.agent.presets import preset_plan
from app.agent.runner import _extraction_failure_message
from app.llm.client import _ensure_follow_link_steps, _parse_actions, recognized_task_plan
from app.llm.schemas import TaskRecognitionError


def test_parse_actions_accepts_model_action_alias():
    # Some models emit "action"; the parser normalizes it to AgentAction.type.
    actions = _parse_actions('[{"action":"goto","url":"https://example.com"}]')

    assert actions[0].type == "goto"
    assert actions[0].url == "https://example.com"


def test_parse_actions_accepts_fenced_json():
    actions = _parse_actions('```json\n[{"type":"goto","url":"https://example.com"}]\n```')

    assert actions[0].type == "goto"
    assert actions[0].url == "https://example.com"


def test_parse_actions_rejects_non_executable_plan():
    with pytest.raises(TaskRecognitionError):
        _parse_actions('[{"type":"ask_user","message":"Which site should I open?"}]')


def test_parse_actions_rejects_disabled_mock_flow():
    with pytest.raises(ValueError, match="Local mock shopping flow"):
        _parse_actions('[{"type":"goto","url":"http://localhost:8000/mock/findparts"}]')


def test_follow_link_repair_expands_single_extract_plan():
    actions = _parse_actions(
        """[
            {"type":"goto","url":"https://example.com/article"},
            {"type":"wait","ms":1000},
            {"type":"extract","target":"First and linked page facts"}
        ]"""
    )

    repaired = _ensure_follow_link_steps("提取当前页面摘要，然后打开 Guido van Rossum 链接并提取他的出生日期。", actions)

    assert [action.type for action in repaired] == ["goto", "wait", "extract", "click", "wait", "extract"]
    assert repaired[2].target == "current page requested fields"
    assert repaired[3].target == "Guido van Rossum"
    assert repaired[5].target == "First and linked page facts"


def test_follow_link_repair_keeps_explicit_navigation_plan():
    actions = _parse_actions(
        """[
            {"type":"goto","url":"https://example.com/article"},
            {"type":"extract","target":"First page facts"},
            {"type":"click","target":"Linked Person"},
            {"type":"wait","ms":1000},
            {"type":"extract","target":"Linked person facts"}
        ]"""
    )

    repaired = _ensure_follow_link_steps("提取当前页面摘要，然后打开 Linked Person 链接并提取他的出生日期。", actions)

    assert repaired == actions


def test_recognized_task_plan_does_not_use_mock_for_default_url():
    actions = recognized_task_plan("Find coffee shops in Seattle.", "http://localhost:8000/mock/findparts")

    assert actions is None


def test_recognized_task_plan_does_not_use_mock_for_aurora_demo():
    actions = recognized_task_plan("Find the AURORA TASK LAMP.", "http://localhost:8000/mock/findparts")

    assert actions is None


def test_recognized_task_plan_handles_chinese_grace_hopper_prompt():
    # Chinese prompts still route to the direct article plan when the entity is recognized.
    actions = recognized_task_plan(
        "打开 `https://www.wikipedia.org/`，搜索 `Grace Hopper`，进入英文条目，提取页面标题、第一段摘要和信息",
        "https://www.wikipedia.org/",
    )

    assert actions is not None
    assert actions[0].type == "goto"
    assert actions[0].url == "https://en.wikipedia.org/wiki/Grace_Hopper"
    assert all(action.type != "fill" for action in actions)


def test_extraction_failure_detects_blocked_page():
    # Bot-wall text should fail the run rather than produce misleading extracted output.
    result = {
        "page_title": "Just a moment...",
        "url": "https://example.com/",
        "heading": "Just a moment...",
        "paragraphs": ["This website verifies you are not a bot."],
        "headings": ["Performing security verification"],
        "links": [],
    }

    assert _extraction_failure_message(result) is not None


def test_extraction_failure_detects_empty_page_summary():
    result = {
        "page_title": "tripadvisor.com",
        "url": "https://www.tripadvisor.com/Search?q=San%20Diego%20attractions",
        "heading": "",
        "paragraphs": [],
        "headings": [],
        "links": [],
    }

    assert _extraction_failure_message(result) is not None


def test_extraction_failure_allows_useful_summary():
    result = {
        "page_title": "Example",
        "url": "https://example.com/",
        "heading": "Example Domain",
        "paragraphs": ["Example Domain is reserved for illustrative examples."],
        "headings": ["Example Domain"],
        "links": [{"text": "More information", "href": "https://www.iana.org/domains/example"}],
    }

    assert _extraction_failure_message(result) is None


def test_preset_planner_outputs_hacker_news_sequence():
    actions = preset_plan("hn-top-story")
    assert actions is not None
    assert [action.type for action in actions] == ["goto", "wait", "extract"]
    assert actions[0].url == "https://news.ycombinator.com/"
    assert actions[2].target == "hacker news top story"


def test_preset_planner_outputs_wikipedia_sequence():
    actions = preset_plan("wikipedia-python-summary")
    assert actions is not None
    assert [action.type for action in actions] == ["goto", "wait", "extract"]
    assert actions[0].url == "https://en.wikipedia.org/wiki/Python_(programming_language)"
    assert actions[2].target == "wikipedia python summary"


def test_preset_planner_outputs_mdn_sequence():
    actions = preset_plan("mdn-api-research")
    assert actions is not None
    assert [action.type for action in actions] == ["goto", "wait", "extract", "goto", "wait", "extract"]
    assert actions[0].url == "https://developer.mozilla.org/en-US/docs/Web/API"
    assert actions[3].url == "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API"
    assert actions[2].target == "mdn web api overview"
    assert actions[5].target == "mdn fetch api detail"
