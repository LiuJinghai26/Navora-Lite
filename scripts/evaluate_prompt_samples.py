#!/usr/bin/env python
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOT = ROOT / "apps" / "server"
sys.path.insert(0, str(SERVER_ROOT))

from app.agent.runner import run_agent  # noqa: E402
from app.config import Settings  # noqa: E402
from app.models import ChatMessage, Run  # noqa: E402
from app.storage.runs_store import RunsStore  # noqa: E402


CATEGORIES = [
    ("with-url/simple", "browser_task_prompts_60.json", ["simple"]),
    ("with-url/medium", "browser_task_prompts_60.json", ["medium"]),
    ("with-url/complex", "browser_task_prompts_60.json", ["complex"]),
    ("no-url/simple", "browser_task_prompts_60_no_url.json", ["simple"]),
    ("no-url/medium", "browser_task_prompts_60_no_url.json", ["medium"]),
    ("no-url/complex", "browser_task_prompts_60_no_url.json", ["complex"]),
    ("multistep", "browser_multistep_prompts_20.json", ["no-url-provided", "url-provided"]),
]

BLOCKED_MARKERS = [
    "captcha",
    "access denied",
    "verify you are human",
    "just a moment",
    "robot or human",
    "are you a robot",
    "request blocked",
    "请求被拦截",
]


def load_items() -> dict[str, list[dict[str, Any]]]:
    by_category: dict[str, list[dict[str, Any]]] = {}
    for category, file_name, section_slugs in CATEGORIES:
        data = json.loads((ROOT / "prompts" / file_name).read_text(encoding="utf-8"))
        items: list[dict[str, Any]] = []
        for section in data["sections"]:
            if section["slug"] not in section_slugs:
                continue
            for prompt in section["prompts"]:
                items.append(
                    {
                        "category": category,
                        "file": file_name,
                        "section": section["slug"],
                        "number": prompt["number"],
                        "task": " ".join(str(prompt["task"]).split()),
                    }
                )
        by_category[category] = items
    return by_category


def pick_samples(items: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if count >= len(items):
        return items
    if count <= 1:
        indexes = [0]
    else:
        indexes = sorted({round(index * (len(items) - 1) / (count - 1)) for index in range(count)})
    return [items[index] for index in indexes[:count]]


def flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(flatten(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {flatten(item)}" for key, item in value.items())
    return str(value)


def expected_terms(task: str) -> list[str]:
    terms = [match.strip() for match in re.findall(r"`([^`]{2,120})`", task)]
    return [term for term in terms if not term.startswith(("http://", "https://"))]


def requested_count(task: str) -> int | None:
    match = re.search(r"(?:前\s*|top\s+)(\d+)", task, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def count_records(value: Any) -> int:
    if isinstance(value, dict):
        total = 0
        for key in ["records", "repositories", "stories", "topics", "links", "extracts"]:
            nested = value.get(key)
            if isinstance(nested, list):
                total = max(total, len(nested))
        return max(total, *(count_records(item) for item in value.values()), 0)
    if isinstance(value, list):
        return max(len(value), *(count_records(item) for item in value), 0)
    return 0


def collect_named_urls(value: Any) -> set[str]:
    urls: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.lower() == "url" and isinstance(nested, str) and nested.startswith(("http://", "https://")):
                urls.add(nested.split("#", 1)[0])
            urls.update(collect_named_urls(nested))
    elif isinstance(value, list):
        for item in value:
            urls.update(collect_named_urls(item))
    return urls


def collect_page_titles(value: Any) -> set[str]:
    titles: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.lower() == "page_title" and isinstance(nested, str) and nested.strip():
                titles.add(nested.strip())
            titles.update(collect_page_titles(nested))
    elif isinstance(value, list):
        for item in value:
            titles.update(collect_page_titles(item))
    return titles


def looks_multipage(task: str) -> bool:
    markers = [
        "打开前",
        "分别进入",
        "分别打开",
        "依次",
        "继续打开",
        "再打开",
        "商品详情页",
        "仓库详情页",
        "三页",
        "三 个",
        "三个",
    ]
    return any(marker in task.lower() for marker in markers)


def judge(task: str, status: str, extracted: Any, failure_type: str | None, steps: list[dict[str, Any]]) -> dict[str, Any]:
    reasons: list[str] = []
    text = flatten(extracted).casefold()
    if status != "completed":
        return {"verdict": "FAIL", "reasons": [f"status={status}", f"failureType={failure_type}"]}
    if extracted in (None, {}, []):
        return {"verdict": "FAIL", "reasons": ["no extracted output"]}
    if any(marker in text for marker in BLOCKED_MARKERS):
        return {"verdict": "FAIL", "reasons": ["blocked/login/captcha marker in output"]}

    terms = expected_terms(task)
    missing = [term for term in terms if term.casefold() not in text]
    if terms and len(missing) == len(terms):
        reasons.append(f"none of expected terms found: {terms[:5]}")
    elif missing:
        reasons.append(f"some expected terms missing: {missing[:5]}")

    count = requested_count(task)
    records = count_records(extracted)
    if count and count <= 10 and records and records < min(count, 5):
        reasons.append(f"requested about {count} items but found {records}")
    urls = collect_named_urls(extracted)
    if count and looks_multipage(task) and urls and len(urls) < min(count, 3):
        reasons.append(f"detail task visited/extracted only {len(urls)} unique URL(s)")
    page_titles = collect_page_titles(extracted)
    if count and looks_multipage(task) and page_titles and len(page_titles) < min(count, 3):
        reasons.append(f"detail task produced only {len(page_titles)} unique page title(s)")

    actions = [step.get("action") for step in steps]
    if looks_multipage(task) and actions.count("extract") < 2:
        reasons.append(f"multi-page/detail task had only {actions.count('extract')} extract step(s)")
    if actions and actions[-1] != "completed":
        reasons.append("timeline does not end with completed")

    if any(reason.startswith("none of expected") for reason in reasons):
        verdict = "FAIL"
    elif reasons:
        verdict = "PARTIAL"
    else:
        verdict = "PASS"
    return {"verdict": verdict, "reasons": reasons}


def run_one(item: dict[str, Any], settings: Settings, store: RunsStore) -> dict[str, Any]:
    run_id = f"eval_{uuid4().hex[:16]}"
    run = Run(
        id=run_id,
        title=f"{item['category']} #{item['number']}",
        task=item["task"],
        url="",
        messages=[
            ChatMessage(
                id=f"msg_{uuid4().hex[:10]}",
                role="user",
                content=item["task"],
                createdAt=datetime.now(timezone.utc).isoformat(),
            )
        ],
        inputs={"category": item["category"], "file": item["file"], "section": item["section"], "number": item["number"]},
    )
    store.create_run(run)
    run_agent(run_id, store, settings)
    final = store.get_run(run_id)
    if final is None:
        raise RuntimeError(f"Run disappeared: {run_id}")
    payload = final.model_dump(mode="json") if hasattr(final, "model_dump") else final.dict()
    steps = payload.get("timeline", [])
    quality = judge(final.task, final.status, final.extracted, final.failureType, steps)
    return {
        **item,
        "run_id": run_id,
        "status": final.status,
        "failureType": final.failureType,
        "timeline_actions": [step["action"] for step in steps],
        "timeline_descriptions": [step["description"] for step in steps],
        "extracted": final.extracted,
        "quality": quality,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run sampled Navora prompt evaluations.")
    parser.add_argument("--samples-per-category", type=int, default=3)
    parser.add_argument("--category", action="append", choices=[category for category, _, _ in CATEGORIES])
    parser.add_argument("--output", default="")
    parser.add_argument("--llm-timeout", type=float, default=90.0)
    args = parser.parse_args()

    selected_categories = set(args.category or [category for category, _, _ in CATEGORIES])
    by_category = load_items()
    output_dir = Path(args.output) if args.output else ROOT / "exports" / f"prompt_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)
    settings = Settings(
        _env_file=SERVER_ROOT / ".env",
        run_storage_path=output_dir / "runs.json",
        artifacts_dir=output_dir / "artifacts",
        runner_step_delay_seconds=0,
        browser_headless=True,
        llm_timeout_seconds=args.llm_timeout,
    )
    store = RunsStore(settings.run_storage_path)

    results: list[dict[str, Any]] = []
    for category in [name for name, _, _ in CATEGORIES if name in selected_categories]:
        samples = pick_samples(by_category[category], args.samples_per_category)
        print(f"## {category} ({len(samples)} samples)", flush=True)
        for item in samples:
            print(f"RUN {category} #{item['number']}: {item['task'][:100]}", flush=True)
            result = run_one(item, settings, store)
            results.append(result)
            quality = result["quality"]
            print(
                f"DONE {result['run_id']} status={result['status']} quality={quality['verdict']} "
                f"actions={result['timeline_actions']} reasons={quality['reasons']}",
                flush=True,
            )
            (output_dir / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    summary: dict[str, dict[str, int]] = {}
    for result in results:
        category = result["category"]
        verdict = result["quality"]["verdict"]
        summary.setdefault(category, {"PASS": 0, "PARTIAL": 0, "FAIL": 0})[verdict] += 1
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir), "summary": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
