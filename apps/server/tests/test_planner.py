from app.llm.client import mock_plan


def test_mock_planner_outputs_demo_sequence():
    actions = mock_plan("http://localhost:8000/mock/findparts")
    assert [action.type for action in actions] == [
        "goto",
        "fill",
        "click",
        "click",
        "fill",
        "click",
        "click",
        "extract",
    ]
    assert actions[1].value == "FIRESTONE W01-377-8537"

