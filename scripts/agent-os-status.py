#!/usr/bin/env python3
"""Print the content-free AgentPlaybook OS runtime status snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_observability import status_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Show AgentPlaybook OS runtime status")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(status_snapshot(args.project), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

