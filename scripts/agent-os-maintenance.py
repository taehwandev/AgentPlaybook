#!/usr/bin/env python3
"""Run bounded Tao Agent OS recovery and retention maintenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_os_maintenance import run_maintenance


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain Tao Agent OS runtime state")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--stale-after-seconds", type=int, default=3600)
    parser.add_argument("--retention-seconds", type=int, default=30 * 24 * 60 * 60)
    parser.add_argument("--max-records", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(run_maintenance(
        args.project,
        retention_seconds=args.retention_seconds,
        stale_after_seconds=args.stale_after_seconds,
        max_records=args.max_records,
    ), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
