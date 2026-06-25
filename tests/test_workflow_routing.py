from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_finish_gate_policy import validate_gate_evidence
from agent_global_lessons import lesson_summary, write_retrospective_candidate
from support.permission_entries import codex_prefix_rule_entries
from workflow_catalog import CONCERNS
from workflow_gate_policy import (
    AMBIGUITY_GATE,
    ALIGNMENT_BRIEF_GATE,
    BOUNDARY_PLAN_GATE,
    DOCUMENTATION_GATE,
    MULTI_AGENT_GATE,
    SIDE_EFFECT_AUDIT_GATE,
    TEST_GATE,
)
from workflow_request import infer_concerns_from_request
from workflow_route import resolve_docs
from workflow_spill import spill_tool_label


class WorkflowRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_state_home = os.environ.get("AGENTPLAYBOOK_STATE_HOME")

    def tearDown(self) -> None:
        if self._old_state_home is None:
            os.environ.pop("AGENTPLAYBOOK_STATE_HOME", None)
        else:
            os.environ["AGENTPLAYBOOK_STATE_HOME"] = self._old_state_home

    def test_testing_concern_is_registered(self) -> None:
        self.assertIn("testing", CONCERNS)
        self.assertIn("common/testing.md", CONCERNS["testing"])
        self.assertIn("common/verification-policy.md", CONCERNS["testing"])

    def test_metering_concern_is_registered_separately_from_design_tokens(self) -> None:
        self.assertIn("metering", CONCERNS)
        self.assertIn("usage", CONCERNS)
        self.assertIn("common/local-tools.md", CONCERNS["metering"])
        self.assertIn("common/local-tools.md", CONCERNS["usage"])
        self.assertIn("common/design-system.md", CONCERNS["tokens"])
        self.assertNotIn("common/local-tools.md", CONCERNS["tokens"])

    def test_spill_request_infers_metering_concern(self) -> None:
        concerns = infer_concerns_from_request("Preserve Spill workflow label bridge data")

        self.assertIn("metering", concerns)

    def test_retrospective_candidate_writes_safe_global_lesson(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["AGENTPLAYBOOK_STATE_HOME"] = temp_dir

            result = write_retrospective_candidate(
                {
                    "retrospective_required": True,
                    "missed_gates": ["side-effect audit"],
                    "gate_signals": [{"gate": "gate evidence policy", "signal": "FAIL"}],
                }
            )

            self.assertTrue(result["created"])
            lesson_path = Path(temp_dir) / result["relative_path"]
            lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
            self.assertEqual("candidate", lesson["promotion_status"])
            self.assertEqual(["side_effect_audit"], lesson["missed_gates"])
            self.assertEqual("safe_slugs_only", lesson["privacy"])
            for private_key in ("project", "path", "prompt", "command", "diff", "repo", "branch"):
                self.assertNotIn(private_key, lesson)

            summary = lesson_summary()
            self.assertEqual(1, summary["candidate_count"])

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

    def test_spill_tool_label_prefers_codex_runtime_over_stale_spill_env(self) -> None:
        label = spill_tool_label({"CODEX_SANDBOX": "seatbelt", "SPILL_AI_TOOL": "claude"})

        self.assertEqual("codex", label)

    def test_spill_tool_label_allows_explicit_agentplaybook_override(self) -> None:
        label = spill_tool_label({"AGENTPLAYBOOK_AI_TOOL": "agy", "CODEX_SANDBOX": "seatbelt"})

        self.assertEqual("antigravity", label)

    def test_code_route_gets_automatic_gates_and_docs(self) -> None:
        route = resolve_docs("feature", None, ["testing"], request_classified=True)

        for gate in (
            AMBIGUITY_GATE,
            DOCUMENTATION_GATE,
            TEST_GATE,
            BOUNDARY_PLAN_GATE,
            MULTI_AGENT_GATE,
            SIDE_EFFECT_AUDIT_GATE,
        ):
            self.assertIn(gate, route["gates"])

        self.assertIn("workflows/ambiguity-gate.md", route["docs"])
        self.assertIn("workflows/documentation-update.md", route["docs"])
        self.assertIn("common/testing.md", route["docs"])
        self.assertIn("common/verification-policy.md", route["docs"])
        self.assertIn("common/code-structure-ownership.md", route["docs"])
        self.assertIn("workflows/multi-agent-collaboration.md", route["docs"])
        self.assertIn("workflows/development-cycle.md", route["docs"])

    def test_prd_and_product_routes_require_alignment_brief(self) -> None:
        prd_route = resolve_docs("prd", None, [], request_classified=True)
        product_route = resolve_docs("product", None, [], request_classified=True)

        self.assertIn(ALIGNMENT_BRIEF_GATE, prd_route["gates"])
        self.assertLess(
            prd_route["gates"].index(ALIGNMENT_BRIEF_GATE),
            prd_route["gates"].index("PRD draft"),
        )
        self.assertIn(ALIGNMENT_BRIEF_GATE, product_route["gates"])
        self.assertLess(
            product_route["gates"].index(ALIGNMENT_BRIEF_GATE),
            product_route["gates"].index("PRD"),
        )

    def test_review_hook_command_requests_code_work_evidence(self) -> None:
        route = resolve_docs("feature", None, ["testing"], request_classified=True)
        review_hook = next(hook for hook in route["hooks"] if hook["hook"] == "review")

        self.assertIn("--boundary-plan-evidence", review_hook["command"])
        self.assertIn("--side-effect-audit-evidence", review_hook["command"])

    def test_triage_does_not_get_code_work_gates(self) -> None:
        route = resolve_docs("triage", None, [], request_classified=True)

        self.assertNotIn(TEST_GATE, route["gates"])
        self.assertNotIn(MULTI_AGENT_GATE, route["gates"])

    def test_finish_policy_rejects_empty_gate_phrases(self) -> None:
        failures = validate_gate_evidence(
            {
                AMBIGUITY_GATE: "done",
                ALIGNMENT_BRIEF_GATE: "done",
                DOCUMENTATION_GATE: "done",
                TEST_GATE: "done",
                BOUNDARY_PLAN_GATE: "done",
                MULTI_AGENT_GATE: "done",
                SIDE_EFFECT_AUDIT_GATE: "done",
            },
            [
                AMBIGUITY_GATE,
                ALIGNMENT_BRIEF_GATE,
                DOCUMENTATION_GATE,
                TEST_GATE,
                BOUNDARY_PLAN_GATE,
                MULTI_AGENT_GATE,
                SIDE_EFFECT_AUDIT_GATE,
            ],
        )

        self.assertEqual(7, len(failures))

    def test_finish_policy_accepts_specific_evidence(self) -> None:
        failures = validate_gate_evidence(
            {
                AMBIGUITY_GATE: "no blockers; safe assumption recorded",
                ALIGNMENT_BRIEF_GATE: (
                    "same understanding: explicit goal captured; may differ: uncertain scope; "
                    "unsupported assumptions: default MVP unless blocker question changes it"
                ),
                DOCUMENTATION_GATE: "updated workflows/README.md",
                TEST_GATE: "unittest tests/test_workflow_routing.py passed",
                BOUNDARY_PLAN_GATE: "existing workflow gate policy boundary; verification via unittest",
                MULTI_AGENT_GATE: "no subagent split: small single-file policy change with same-file scope",
                SIDE_EFFECT_AUDIT_GATE: "final diff checked; no unexpected generated files or lockfile changes",
            },
            [
                AMBIGUITY_GATE,
                ALIGNMENT_BRIEF_GATE,
                DOCUMENTATION_GATE,
                TEST_GATE,
                BOUNDARY_PLAN_GATE,
                MULTI_AGENT_GATE,
                SIDE_EFFECT_AUDIT_GATE,
            ],
        )

        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
