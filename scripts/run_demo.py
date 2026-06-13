#!/usr/bin/env python
import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def request_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Navora Lite demo task.")
    parser.add_argument("--task", default="Find the AURORA TASK LAMP, choose Warm White, set quantity to 2, add it to the cart, and extract the cart summary")
    parser.add_argument("--url", default="http://localhost:8000/mock/findparts")
    parser.add_argument("--api-base", default="http://localhost:8000")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    try:
        created = request_json("POST", f"{args.api_base}/api/runs", {"task": args.task, "url": args.url})
    except urllib.error.URLError as exc:
        print(f"Could not reach Navora Lite server: {exc}", file=sys.stderr)
        return 1

    run_id = created["run_id"]
    print(f"Created run: {run_id}")
    deadline = time.time() + args.timeout
    # Polling keeps the CLI dependency-free; the web UI uses SSE for richer updates.
    while time.time() < deadline:
        run = request_json("GET", f"{args.api_base}/api/runs/{run_id}")
        print(f"status={run['status']} steps={len(run['timeline'])}")
        if run["status"] in {"completed", "failed", "stopped"}:
            print(json.dumps({"run_id": run_id, "status": run["status"], "extracted": run.get("extracted")}, indent=2))
            return 0 if run["status"] == "completed" else 2
        time.sleep(1)

    print(f"Timed out waiting for {run_id}", file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
