from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import runs
from app.main import app


client = TestClient(app)


def test_runs_api_create_get_stop():
    response = client.post(
        "/api/runs",
        json={
            "task": "Open Hacker News and extract the current top story.",
            "url": "https://news.ycombinator.com/",
            "auto_start": False,
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    get_response = client.get(f"/api/runs/{run_id}")
    assert get_response.status_code == 200
    assert get_response.json()["task"].startswith("Open Hacker News")

    stop_response = client.post(f"/api/runs/{run_id}/stop")
    assert stop_response.status_code == 200
    assert stop_response.json()["stopRequested"] is True


def test_runs_api_preserves_preset_metadata():
    response = client.post(
        "/api/runs",
        json={
            "task": "Open Hacker News and extract the current top story.",
            "url": "https://news.ycombinator.com/",
            "preset_id": "hn-top-story",
            "auto_start": False,
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    get_response = client.get(f"/api/runs/{run_id}")
    assert get_response.status_code == 200
    run = get_response.json()
    assert run["title"] == "Hacker News Top Story"
    assert run["inputs"]["preset_id"] == "hn-top-story"


def test_runs_api_requires_model_config_for_auto_started_free_task(monkeypatch):
    monkeypatch.setattr(
        runs,
        "get_settings",
        lambda: SimpleNamespace(
            api_base="",
            api_key="",
            model_provider="openai-compatible",
            model_name="qwen3-32b",
            browser_channel="chromium",
        ),
    )

    response = client.post(
        "/api/runs",
        json={
            "task": "Open https://example.com and extract the page title.",
            "auto_start": True,
        },
    )

    assert response.status_code == 400
    assert "配置模型 API" in response.json()["detail"]


def test_runs_api_infers_start_url_from_task_text():
    response = client.post(
        "/api/runs",
        json={
            "task": "Open https://example.com and extract the page title.",
            "auto_start": False,
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    get_response = client.get(f"/api/runs/{run_id}")
    assert get_response.status_code == 200
    assert get_response.json()["url"] == "https://example.com"


def test_runs_api_clears_disabled_mock_url_without_task_url():
    response = client.post(
        "/api/runs",
        json={
            "task": "Search the public web for browser automation news.",
            "url": "http://localhost:8000/mock/findparts",
            "auto_start": False,
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    get_response = client.get(f"/api/runs/{run_id}")
    assert get_response.status_code == 200
    assert get_response.json()["url"] == ""


def test_mock_page_is_removed():
    response = client.get("/mock/findparts")
    assert response.status_code == 404


def test_tasks_api_lists_run_history():
    create_response = client.post(
        "/api/runs",
        json={
            "task": "Open Hacker News and extract the current top story.",
            "url": "https://news.ycombinator.com/",
            "auto_start": False,
        },
    )
    assert create_response.status_code == 200

    response = client.get("/api/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert any(item["id"] == create_response.json()["run_id"] for item in tasks)


def test_tasks_api_deletes_run_history_item():
    create_response = client.post(
        "/api/runs",
        json={
            "task": "Open Hacker News and extract the current top story.",
            "url": "https://news.ycombinator.com/",
            "auto_start": False,
        },
    )
    assert create_response.status_code == 200
    run_id = create_response.json()["run_id"]

    delete_response = client.delete(f"/api/tasks/{run_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/runs/{run_id}")
    assert get_response.status_code == 404
