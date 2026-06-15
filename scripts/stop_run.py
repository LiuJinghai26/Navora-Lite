#!/usr/bin/env python
import argparse
import json
import urllib.request


def main() -> int:
    # Stop requests are idempotent from the caller's perspective; the server owns final state.
    parser = argparse.ArgumentParser(description="Stop a Navora Lite run.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--api-base", default="http://localhost:8000")
    args = parser.parse_args()

    request = urllib.request.Request(f"{args.api_base}/api/runs/{args.run_id}/stop", method="POST")
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=15) as response:
        print(json.dumps(json.loads(response.read().decode("utf-8")), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
