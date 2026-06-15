import pytest

from app.agent.browser import preset_fallback_html
from app.agent.presets import preset_plan
from app.agent.runner import _extraction_failure_message
from app.llm.client import _parse_actions, mock_plan, recognized_task_plan
from app.llm.schemas import TaskRecognitionError


def test_mock_planner_outputs_demo_sequence():
    actions = mock_plan("http://localhost:8000/mock/findparts")
    assert [action.type for action in actions] == [
        "goto",
        "fill",
        "click",
        "click",
        "click",
        "fill",
        "click",
        "click",
        "extract",
    ]
    assert actions[1].value == "AURORA TASK LAMP"
    assert actions[4].target == "color Warm White"


def test_parse_actions_accepts_model_action_alias():
    actions = _parse_actions('[{"action":"goto","url":"http://localhost:8000/mock/findparts"}]')

    assert actions[0].type == "goto"
    assert actions[0].url == "http://localhost:8000/mock/findparts"


def test_parse_actions_accepts_fenced_json():
    actions = _parse_actions('```json\n[{"type":"goto","url":"https://example.com"}]\n```')

    assert actions[0].type == "goto"
    assert actions[0].url == "https://example.com"


def test_parse_actions_rejects_non_executable_plan():
    with pytest.raises(TaskRecognitionError):
        _parse_actions('[{"type":"ask_user","message":"Which site should I open?"}]')


def test_recognized_task_plan_does_not_use_mock_for_default_url():
    actions = recognized_task_plan("Find coffee shops in Seattle.", "http://localhost:8000/mock/findparts")

    assert actions is None


def test_recognized_task_plan_uses_mock_only_for_aurora_demo():
    actions = recognized_task_plan("Find the AURORA TASK LAMP.", "http://localhost:8000/mock/findparts")

    assert actions is not None
    assert actions[1].value == "AURORA TASK LAMP"


def test_extraction_failure_detects_blocked_page():
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


def test_preset_fallback_pages_support_extractors():
    hacker_news = preset_fallback_html("https://news.ycombinator.com/")
    wikipedia = preset_fallback_html("https://en.wikipedia.org/wiki/Python_(programming_language)")
    mdn_index = preset_fallback_html("https://developer.mozilla.org/en-US/docs/Web/API")
    mdn_fetch = preset_fallback_html("https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API")
    httpbin_form = preset_fallback_html("https://httpbin.org/forms/post")

    assert hacker_news is not None and "class=\"athing\"" in hacker_news
    assert wikipedia is not None and "id=\"firstHeading\"" in wikipedia
    assert mdn_index is not None and "/Web/API/Fetch_API" in mdn_index
    assert mdn_fetch is not None and "<h1>Fetch API</h1>" in mdn_fetch
    assert httpbin_form is not None and 'name="custname"' in httpbin_form
