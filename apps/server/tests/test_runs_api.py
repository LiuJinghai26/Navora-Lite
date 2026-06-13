from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_runs_api_create_get_stop():
    response = client.post(
        "/api/runs",
        json={
            "task": "Find the AURORA TASK LAMP, choose Warm White, set quantity to 2, add it to the cart, and extract the cart summary",
            "url": "http://localhost:8000/mock/findparts",
            "auto_start": False,
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    get_response = client.get(f"/api/runs/{run_id}")
    assert get_response.status_code == 200
    assert get_response.json()["task"].startswith("Find the AURORA")

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


def test_mock_page_contains_demo_controls():
    response = client.get("/mock/findparts")
    assert response.status_code == 200
    html = response.text
    assert 'id="search-input"' in html
    assert 'data-testid="product-link"' in html
    assert 'id="color-warm-white"' in html
    assert 'id="quantity"' in html


def test_tasks_api_lists_run_history():
    create_response = client.post(
        "/api/runs",
        json={
            "task": "Find the AURORA TASK LAMP, choose Warm White, set quantity to 2, add it to the cart, and extract the cart summary",
            "url": "http://localhost:8000/mock/findparts",
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
            "task": "Find the AURORA TASK LAMP, choose Warm White, set quantity to 2, add it to the cart, and extract the cart summary",
            "url": "http://localhost:8000/mock/findparts",
            "auto_start": False,
        },
    )
    assert create_response.status_code == 200
    run_id = create_response.json()["run_id"]

    delete_response = client.delete(f"/api/tasks/{run_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/runs/{run_id}")
    assert get_response.status_code == 404
