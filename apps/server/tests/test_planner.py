from app.agent.browser import preset_fallback_html
from app.agent.presets import preset_plan
from app.llm.client import _parse_actions, fallback_plan, mock_plan


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


def test_fallback_planner_uses_wikipedia_article_for_real_wiki_task():
    actions = fallback_plan(
        "Open wikipedia.org, search Ada Lovelace, and extract title, summary, and birth date.",
        "https://www.wikipedia.org/",
    )

    assert [action.type for action in actions] == ["goto", "wait", "extract"]
    assert actions[0].url == "https://en.wikipedia.org/wiki/Ada_Lovelace"
    assert actions[2].target == "wikipedia article summary"
    assert all(action.value != "AURORA TASK LAMP" for action in actions)


def test_fallback_planner_keeps_unknown_real_sites_read_only():
    actions = fallback_plan("Extract the visible page summary.", "https://example.com/")

    assert [action.type for action in actions] == ["goto", "wait", "extract"]
    assert actions[0].url == "https://example.com/"
    assert actions[2].target == "page summary"


def test_fallback_planner_supports_httpbin_test_form():
    actions = fallback_plan("Fill and submit the public httpbin test form.", "https://httpbin.org/forms/post")

    assert actions[0].url == "https://httpbin.org/forms/post"
    assert actions[-1].target == "httpbin form echo"
    assert any(action.selector == 'input[name="custemail"]' for action in actions)
