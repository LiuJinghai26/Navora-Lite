from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import runs, tasks
from app.main import app


client = TestClient(app)


def test_runs_api_create_get_stop():
    # Basic lifecycle coverage for an idle run that does not start the browser.
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
    # Free-form auto-start is blocked without model settings.
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
    # The disabled local shopping demo should stay unreachable.
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


def test_tasks_api_lists_batch_prompt_sources():
    response = client.get("/api/tasks/batch-prompts")

    assert response.status_code == 200
    sources = response.json()
    assert any(item["id"] == "all" and item["count"] == 140 for item in sources)
    assert any(item["id"] == "browser_task_prompts_60.md" and item["count"] == 60 for item in sources)
    assert any(
        item["id"] == "browser_task_prompts_60.md#simple"
        and item["title"] == "60 prompts with URLs - Simple"
        and item["count"] == 20
        and item["file"] == "browser_task_prompts_60.md"
        and item["section"] == "simple"
        for item in sources
    )
    assert any(item["id"] == "browser_task_prompts_60.md#medium" and item["count"] == 20 for item in sources)
    assert any(item["id"] == "browser_task_prompts_60.md#complex" and item["count"] == 20 for item in sources)
    assert any(item["id"] == "browser_task_prompts_60_no_url.md#simple" and item["count"] == 20 for item in sources)
    assert any(item["id"] == "browser_task_prompts_60_no_url.md#medium" and item["count"] == 20 for item in sources)
    assert any(item["id"] == "browser_task_prompts_60_no_url.md#complex" and item["count"] == 20 for item in sources)
    assert any(item["id"] == "browser_multistep_prompts_20.md" and item["count"] == 20 for item in sources)
    assert any(item["id"] == "browser_multistep_prompts_20.md#no-url-provided" and item["count"] == 10 for item in sources)
    assert any(item["id"] == "browser_multistep_prompts_20.md#url-provided" and item["count"] == 10 for item in sources)


def test_batch_prompt_sections_are_read_from_markdown_headings():
    prompts = tasks._parse_markdown_prompt_items(
        "sample.md",
        """# Prompt Suite
## Easy Mode

1. First task.

2. Second task.

### Hard Mode

3. Third task.
""",
    )

    assert tasks._prompt_section_summaries(prompts) == [
        tasks.PromptSection("easy-mode", "Easy Mode", 2),
        tasks.PromptSection("hard-mode", "Hard Mode", 1),
    ]


def test_batch_prompt_parser_preserves_multiline_prompt_text():
    prompts = tasks._parse_markdown_prompt_items(
        "sample.md",
        """# Prompt Suite
## Complex

1. 打开 Example 搜索 `alpha`，
   再打开第一个详情页，
   最后提取标题和摘要。

2. 打开第二个页面并提取标题。
""",
    )

    assert len(prompts) == 2
    assert prompts[0].section == "complex"
    assert prompts[0].section_title == "Complex"
    assert prompts[0].task == "打开 Example 搜索 `alpha`， 再打开第一个详情页， 最后提取标题和摘要。"


def test_tasks_api_creates_batch_tasks():
    response = client.post(
        "/api/tasks/batch-tests",
        json={"source": "browser_task_prompts_60.md", "limit": 2, "offset": 0},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert len(payload["run_ids"]) == 2

    first_run = client.get(f"/api/runs/{payload['run_ids'][0]}").json()
    assert first_run["status"] == "idle"
    assert first_run["url"] == "https://www.wikipedia.org/"
    assert first_run["inputs"]["batch_source"] == "browser_task_prompts_60.md"


def test_tasks_api_creates_batch_tasks_from_section():
    response = client.post(
        "/api/tasks/batch-tests",
        json={"source": "browser_task_prompts_60.md#complex", "limit": 1, "offset": 0},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1

    first_run = client.get(f"/api/runs/{payload['run_ids'][0]}").json()
    assert first_run["inputs"]["batch_suite"] == "browser_task_prompts_60.md#complex"
    assert first_run["inputs"]["batch_source"] == "browser_task_prompts_60.md"
    assert first_run["inputs"]["batch_section"] == "complex"
    assert first_run["inputs"]["batch_prompt_number"] == 41


def test_tasks_api_creates_all_remaining_batch_and_schedules_sequential_run(monkeypatch):
    scheduled: list[list[str]] = []
    monkeypatch.setattr(tasks, "_run_batch_tasks", lambda run_ids, store, settings: scheduled.append(run_ids))

    response = client.post(
        "/api/tasks/batch-tests",
        json={
            "source": "browser_multistep_prompts_20.md",
            "offset": 18,
            "all_remaining": True,
            "run_sequentially": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert payload["run_sequentially"] is True
    assert scheduled == [payload["run_ids"]]

    first_run = client.get(f"/api/runs/{payload['run_ids'][0]}").json()
    assert first_run["status"] == "idle"
    assert first_run["inputs"]["batch_suite"] == "browser_multistep_prompts_20.md"
    assert first_run["inputs"]["batch_prompt_number"] == 19


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
