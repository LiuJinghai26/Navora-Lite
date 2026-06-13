from app.agent.presets import preset_plan
from app.llm.client import mock_plan


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
