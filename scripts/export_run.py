#!/usr/bin/env python
import argparse
import json
from pathlib import Path
import urllib.request


def main() -> int:
    # Export the backend's canonical run JSON without altering local server state.
    parser = argparse.ArgumentParser(description="Export a Navora Lite run as JSON.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--api-base", default="http://localhost:8000")
    args = parser.parse_args()

    with urllib.request.urlopen(f"{args.api_base}/api/runs/{args.run_id}", timeout=15) as response:
        run = json.loads(response.read().decode("utf-8"))
    output = Path(args.output)
    # Create parent directories so exports can target a fresh folder.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(f"Exported {args.run_id} to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
