#!/usr/bin/env python3
"""Configure AI runtime hooks and permissions for AgentPlaybook.

Run once after cloning AgentPlaybook to allow the AgentPlaybook Python
entrypoints in local agent runtimes. When the optional local Spill helper is
installed, this also wires AgentPlaybook's workflow label bridge. Re-running is
safe; existing hooks and permissions are deduplicated.

Usage:
    python3 scripts/setup-agent-hooks.py
    python3 scripts/setup-agent-hooks.py --dry-run
    python3 scripts/setup-agent-hooks.py --check
"""

from __future__ import annotations

from support.setup_agent_hooks_impl import main


if __name__ == "__main__":
    main()
