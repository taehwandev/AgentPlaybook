from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_finish_gate_policy import validate_gate_evidence
from support.permission_entries import codex_prefix_rule_entries
from workflow_catalog import CONCERNS
from workflow_gate_policy import (
    AMBIGUITY_GATE,
    DOCUMENTATION_GATE,
    MULTI_AGENT_GATE,
    TEST_GATE,
)
from workflow_route import resolve_docs


class WorkflowRoutingTests(unittest.TestCase):
    def test_testing_concern_is_registered(self) -> None:
        self.assertIn("testing", CONCERNS)
        self.assertIn("common/testing.md", CONCERNS["testing"])
        self.assertIn("common/verification-policy.md", CONCERNS["testing"])

    def test_setup_permissions_include_new_workflow_helpers(self) -> None:
        entries = "\n".join(codex_prefix_rule_entries(ROOT / "scripts"))

        self.assertIn("workflow_gate_policy.py", entries)
        self.assertIn("workflow_concern_docs.py", entries)
        self.assertIn("agent_finish_gate_policy.py", entries)
        self.assertIn("agent_finish_common.py", entries)
        self.assertIn("agent_finish_check_steps.py", entries)
        self.assertIn("agent_finish_final_checks.py", entries)
        self.assertIn("$AGENTPLAYBOOK_HOME/scripts/agent-hook.py", entries)
        self.assertIn("${AGENTPLAYBOOK_HOME}/scripts/agent-hook.py", entries)

    def test_code_route_gets_automatic_gates_and_docs(self) -> None:
        route = resolve_docs("feature", None, ["testing"], request_classified=True)

        for gate in (AMBIGUITY_GATE, DOCUMENTATION_GATE, TEST_GATE, MULTI_AGENT_GATE):
            self.assertIn(gate, route["gates"])

        self.assertIn("workflows/ambiguity-gate.md", route["docs"])
        self.assertIn("workflows/documentation-update.md", route["docs"])
        self.assertIn("common/testing.md", route["docs"])
        self.assertIn("common/verification-policy.md", route["docs"])
        self.assertIn("workflows/multi-agent-collaboration.md", route["docs"])

    def test_triage_does_not_get_code_work_gates(self) -> None:
        route = resolve_docs("triage", None, [], request_classified=True)

        self.assertNotIn(TEST_GATE, route["gates"])
        self.assertNotIn(MULTI_AGENT_GATE, route["gates"])

    def test_finish_policy_rejects_empty_gate_phrases(self) -> None:
        failures = validate_gate_evidence(
            {
                AMBIGUITY_GATE: "done",
                DOCUMENTATION_GATE: "done",
                TEST_GATE: "done",
                MULTI_AGENT_GATE: "done",
            },
            [AMBIGUITY_GATE, DOCUMENTATION_GATE, TEST_GATE, MULTI_AGENT_GATE],
        )

        self.assertEqual(4, len(failures))

    def test_finish_policy_accepts_specific_evidence(self) -> None:
        failures = validate_gate_evidence(
            {
                AMBIGUITY_GATE: "no blockers; safe assumption recorded",
                DOCUMENTATION_GATE: "updated workflows/README.md",
                TEST_GATE: "unittest tests/test_workflow_routing.py passed",
                MULTI_AGENT_GATE: "serial: small single-file policy change with same-file scope",
            },
            [AMBIGUITY_GATE, DOCUMENTATION_GATE, TEST_GATE, MULTI_AGENT_GATE],
        )

        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
