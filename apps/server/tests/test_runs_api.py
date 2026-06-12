from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_runs_api_create_get_stop():
    response = client.post(
        "/api/runs",
        json={
            "task": "Add FIRESTONE W01-377-8537 to the cart and set quantity to 1",
            "url": "http://localhost:8000/mock/findparts",
            "auto_start": False,
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    get_response = client.get(f"/api/runs/{run_id}")
    assert get_response.status_code == 200
    assert get_response.json()["task"].startswith("Add FIRESTONE")

    stop_response = client.post(f"/api/runs/{run_id}/stop")
    assert stop_response.status_code == 200
    assert stop_response.json()["stopRequested"] is True


def test_mock_page_contains_demo_controls():
    response = client.get("/mock/findparts")
    assert response.status_code == 200
    html = response.text
    assert 'id="search-input"' in html
    assert 'data-testid="product-link"' in html
    assert 'id="quantity"' in html
