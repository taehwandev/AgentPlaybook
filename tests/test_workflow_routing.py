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
from agent_finish_check_steps import check_request_intake, validate_grill_me_skill_evidence
from agent_global_lessons import lesson_summary, write_retrospective_candidate
from agent_preflight_runtime import (
    AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES as PREFLIGHT_AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES,
)
from support.agy_setup import AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES, _agy_runtime_bridge_block
from support.permission_entries import codex_prefix_rule_entries
from workflow_catalog import COMMANDS, CONCERNS
from workflow_gate_policy import (
    AMBIGUITY_GATE,
    ALIGNMENT_BRIEF_GATE,
    BOUNDARY_PLAN_GATE,
    DOCUMENTATION_GATE,
    MULTI_AGENT_GATE,
    ROUTE_DOCS_READ_GATE,
    SIDE_EFFECT_AUDIT_GATE,
    TEST_GATE,
    ALIGNMENT_BRIEF_COMMANDS,
)
from workflow_request import infer_concerns_from_request
from workflow_request import classify_request
from workflow_route import resolve_docs
from workflow_spill import spill_tool_label
from workflow_validate import STRICT_CARD_REQUIRED_HEADINGS


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
        self.assertIn("definition-of-done", CONCERNS)
        self.assertIn("common/definition-of-done.md", CONCERNS["definition-of-done"])

    def test_lifecycle_alias_commands_are_registered(self) -> None:
        for command in ("spec", "plan", "build", "test", "webperf", "code-simplify", "ship"):
            with self.subTest(command=command):
                self.assertIn(command, COMMANDS)
                route = resolve_docs(command, None, [], request_classified=True)

                self.assertIn("request intake", route["gates"])
                self.assertIn(ROUTE_DOCS_READ_GATE, route["gates"])

        self.assertIn("common/incremental-implementation.md", resolve_docs("build", None, [], request_classified=True)["docs"])
        self.assertIn("common/web-performance-verification.md", resolve_docs("webperf", None, [], request_classified=True)["docs"])
        self.assertIn("common/ci-cd-automation.md", resolve_docs("ship", None, [], request_classified=True)["docs"])

        webperf_route = resolve_docs("webperf", None, [], request_classified=True)
        self.assertLess(webperf_route["gates"].index(ROUTE_DOCS_READ_GATE), webperf_route["gates"].index("baseline"))
        self.assertLess(webperf_route["gates"].index(ALIGNMENT_BRIEF_GATE), webperf_route["gates"].index("baseline"))

        spec_route = resolve_docs("spec", None, [], request_classified=True)
        self.assertLess(spec_route["gates"].index(ROUTE_DOCS_READ_GATE), spec_route["gates"].index("local product docs"))
        self.assertLess(spec_route["gates"].index(ROUTE_DOCS_READ_GATE), spec_route["gates"].index("ambiguity check"))

    def test_agent_skills_gap_concerns_are_registered(self) -> None:
        expected = {
            "skill-card": "common/agent-skill-card-anatomy.md",
            "source-driven": "common/source-driven-development.md",
            "doubt-driven": "common/doubt-driven-development.md",
            "incremental": "common/incremental-implementation.md",
            "deprecation": "common/deprecation-migration.md",
            "ci": "common/ci-cd-automation.md",
            "webperf": "common/web-performance-verification.md",
            "browser-testing": "common/browser-runtime-testing.md",
        }

        for concern, doc in expected.items():
            with self.subTest(concern=concern):
                self.assertIn(concern, CONCERNS)
                self.assertIn(doc, CONCERNS[concern])

    def test_strict_card_required_headings_cover_anti_rationalization(self) -> None:
        self.assertIn("## Common Rationalizations", STRICT_CARD_REQUIRED_HEADINGS)
        self.assertIn("## Red Flags", STRICT_CARD_REQUIRED_HEADINGS)
        self.assertIn("## Verification", STRICT_CARD_REQUIRED_HEADINGS)

    def test_metering_concern_is_registered_separately_from_design_tokens(self) -> None:
        self.assertIn("metering", CONCERNS)
        self.assertIn("usage", CONCERNS)
        self.assertIn("common/local-tools.md", CONCERNS["metering"])
        self.assertIn("docs/agent-runtime-integration.md", CONCERNS["local-tools"])
        self.assertIn("common/local-tools.md", CONCERNS["usage"])
        self.assertIn("common/design-system.md", CONCERNS["tokens"])
        self.assertNotIn("common/local-tools.md", CONCERNS["tokens"])

    def test_spill_request_infers_metering_concern(self) -> None:
        concerns = infer_concerns_from_request("Preserve Spill workflow label bridge data")

        self.assertIn("metering", concerns)

    def test_agent_skills_gap_requests_infer_new_concerns(self) -> None:
        examples = (
            ("Add a definition of done checklist", "testing"),
            ("Review web performance and Core Web Vitals", "webperf"),
            ("Review Jetpack Compose recomposition performance", "compose"),
            ("Review Jetpack Compose recomposition performance", "performance"),
            ("Use official docs for this SDK change", "source-driven"),
            ("Run a doubt-driven assumption review", "doubt-driven"),
            ("Split this into vertical slices", "incremental"),
            ("Fix CI/CD automation", "ci"),
        )

        for request, concern in examples:
            with self.subTest(request=request):
                self.assertIn(concern, infer_concerns_from_request(request))

    def test_writing_requests_infer_human_authored_writing_concern(self) -> None:
        examples = (
            "AgentPlaybook 소개하는 글을 써줘. 바이브가드도 같이 소개해줘.",
            "블로그 글 써달라고 하면 공유 writing workspace에 초안을 저장하게 해줘.",
            "AI 티 덜 나게 문체를 다듬어줘.",
            "Write an article introducing AgentPlaybook and VibeGuard.",
            "Draft release notes with a less AI-sounding tone.",
        )

        for request in examples:
            with self.subTest(request=request):
                concerns = infer_concerns_from_request(request)
                self.assertIn("writing", concerns)

        route = resolve_docs("docs", None, ["writing"], request_classified=True)
        self.assertIn("common/human-authored-writing.md", route["docs"])
        self.assertIn("common/writing-workspace.md", route["docs"])

    def test_android_performance_route_loads_external_skill_manifest(self) -> None:
        route = resolve_docs(
            "workflow-setup",
            "android",
            ["performance"],
            request_classified=True,
        )

        self.assertIn("platforms/android/android-compose-ui.md", route["docs"])
        self.assertIn("platforms/android/android-review.md", route["docs"])
        self.assertIn("platforms/android/android-external-skill-source-coverage.md", route["docs"])

    def test_android_platform_surfaces_load_external_skill_manifest(self) -> None:
        for concern in ("architecture", "security", "testing", "module", "dependency", "migration", "devtools"):
            with self.subTest(concern=concern):
                route = resolve_docs(
                    "workflow-setup",
                    "android",
                    [concern],
                    request_classified=True,
                )

                self.assertIn("platforms/android/android-external-skill-source-coverage.md", route["docs"])

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

    def test_agy_runtime_bridge_requires_project_discovery_entry(self) -> None:
        required = [
            "If the runtime starts outside the target repo or the target repo is not explicit, run AgentPlaybook agent-entry.py or project-discover.py before project work.",
            "If project discovery returns ambiguous or not_found, ask the user for the target project before routing, editing, testing, committing, or reporting completion.",
        ]
        block = _agy_runtime_bridge_block(ROOT)

        for phrase in required:
            self.assertIn(phrase, AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES)
            self.assertIn(phrase, PREFLIGHT_AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES)
            self.assertIn(phrase, block)

    def test_spill_tool_label_prefers_codex_runtime_over_stale_spill_env(self) -> None:
        label = spill_tool_label({"CODEX_SANDBOX": "seatbelt", "SPILL_AI_TOOL": "claude"})

        self.assertEqual("codex", label)

    def test_spill_tool_label_allows_explicit_agentplaybook_override(self) -> None:
        label = spill_tool_label({"AGENTPLAYBOOK_AI_TOOL": "agy", "CODEX_SANDBOX": "seatbelt"})

        self.assertEqual("antigravity", label)

    def test_code_route_gets_automatic_gates_and_docs(self) -> None:
        route = resolve_docs("feature", None, ["testing"], request_classified=True)

        for gate in (
            ROUTE_DOCS_READ_GATE,
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
        self.assertLess(
            route["gates"].index(ROUTE_DOCS_READ_GATE),
            route["gates"].index("PRD/ARD applicability"),
        )
        self.assertLess(route["gates"].index(ROUTE_DOCS_READ_GATE), route["gates"].index(AMBIGUITY_GATE))
        self.assertLess(route["gates"].index(ROUTE_DOCS_READ_GATE), route["gates"].index("implementation"))

    def test_workspace_scope_checkpoint_evidence_is_validated_when_present(self) -> None:
        failures = validate_gate_evidence(
            {
                "workspace scope checkpoint": (
                    "starting primary repo: app; secondary repo/source of truth: web; "
                    "mode: primary-led secondary write; verification: web test plus app smoke"
                )
            },
            [],
        )

        self.assertEqual([], failures)

        failures = validate_gate_evidence(
            {"workspace scope checkpoint": "primary repo: app; secondary repo: web"},
            [],
        )

        self.assertTrue(any("workspace scope checkpoint evidence" in failure for failure in failures))

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
        self.assertIn("workflows/prd-creation.md", prd_route["docs"])
        self.assertIn("workflows/prd-creation.md", product_route["docs"])

    def test_modify_and_analysis_routes_require_alignment_brief(self) -> None:
        for command in sorted(ALIGNMENT_BRIEF_COMMANDS):
            with self.subTest(command=command):
                route = resolve_docs(command, None, [], request_classified=True)

                self.assertIn(ALIGNMENT_BRIEF_GATE, route["gates"])

    def test_feature_alignment_runs_before_acceptance_criteria(self) -> None:
        route = resolve_docs("feature", None, [], request_classified=True)

        self.assertLess(
            route["gates"].index(ALIGNMENT_BRIEF_GATE),
            route["gates"].index("acceptance criteria"),
        )
        self.assertIn("common/task-intake-effort-routing.md", route["docs"])

    def test_grill_me_request_uses_triage_and_grill_gate(self) -> None:
        classification = classify_request("그릴미 해줘")
        route = resolve_docs("triage", None, [], request_classified=True)

        self.assertTrue(classification["grill_me"])
        self.assertTrue(classification["question_drill"])
        self.assertEqual("triage", classification["recommended_route"])
        self.assertIn("grill-me if needed", route["gates"])

    def test_grill_me_policy_mention_does_not_require_grill_session(self) -> None:
        classification = classify_request("`scripts/workflow_request.py`의 grill-me skill evidence policy를 수정해줘")

        self.assertFalse(classification["grill_me"])
        self.assertEqual("work", classification["response_mode"])

    def test_grill_me_evidence_requires_skill_session(self) -> None:
        self.assertEqual(
            [
                "Grill-Me evidence must name the Grill-Me skill or /grilling session and its output; "
                "manual blocker questions alone are not enough"
            ],
            validate_grill_me_skill_evidence("asked blocker questions manually"),
        )
        self.assertEqual(
            [],
            validate_grill_me_skill_evidence(
                "Grill-Me skill /grilling session output completed: asked one blocker question "
                "with recommended answer and decisions resolved"
            ),
        )

    def test_invalid_grill_me_finish_evidence_is_missed_gate(self) -> None:
        gate_signals: list[dict[str, str]] = []
        missed_gates: list[str] = []
        failures: list[str] = []

        required = check_request_intake(
            {},
            {"request": "그릴미 해줘"},
            {},
            {"grill-me if needed": "asked blocker questions manually"},
            gate_signals,
            missed_gates,
            failures,
        )

        self.assertTrue(required)
        self.assertIn("grill-me", missed_gates)
        self.assertTrue(any("manual blocker questions alone are not enough" in failure for failure in failures))

    def test_grill_me_policy_classification_evidence_does_not_require_session(self) -> None:
        gate_signals: list[dict[str, str]] = []
        missed_gates: list[str] = []
        failures: list[str] = []

        required = check_request_intake(
            {},
            {
                "request_classified": True,
                "classification_evidence": (
                    "clear-scoped workflow policy update: Grill-Me means the grill-me skill "
                    "/grilling session; current work updates evidence policy"
                ),
            },
            {},
            {},
            gate_signals,
            missed_gates,
            failures,
        )

        self.assertFalse(required)
        self.assertNotIn("grill-me", missed_gates)
        self.assertFalse(any("Grill-Me skill was required" in failure for failure in failures))

    def test_grill_me_classification_boolean_requires_finish_evidence(self) -> None:
        gate_signals: list[dict[str, str]] = []
        missed_gates: list[str] = []
        failures: list[str] = []
        classification = classify_request("고쳐줘")

        required = check_request_intake(
            {},
            {"request": "고쳐줘"},
            classification,
            {},
            gate_signals,
            missed_gates,
            failures,
        )

        self.assertTrue(classification["grill_me"])
        self.assertTrue(required)
        self.assertIn("grill-me", missed_gates)
        self.assertTrue(any("Grill-Me skill was required" in failure for failure in failures))

    def test_analysis_and_setup_alignment_runs_before_work_gates(self) -> None:
        planning_route = resolve_docs("planning", None, [], request_classified=True)
        release_route = resolve_docs("release", None, [], request_classified=True)
        multi_agent_route = resolve_docs("multi-agent", None, [], request_classified=True)

        self.assertLess(
            planning_route["gates"].index(ALIGNMENT_BRIEF_GATE),
            planning_route["gates"].index("sources"),
        )
        self.assertLess(
            release_route["gates"].index(ALIGNMENT_BRIEF_GATE),
            release_route["gates"].index("package"),
        )
        self.assertLess(
            multi_agent_route["gates"].index(ALIGNMENT_BRIEF_GATE),
            multi_agent_route["gates"].index("roles"),
        )

    def test_review_hook_command_requests_code_work_evidence(self) -> None:
        route = resolve_docs("feature", None, ["testing"], request_classified=True)
        review_hook = next(hook for hook in route["hooks"] if hook["hook"] == "review")

        self.assertIn("--boundary-plan-evidence", review_hook["command"])
        self.assertIn("--side-effect-audit-evidence", review_hook["command"])

    def test_triage_does_not_get_code_work_gates(self) -> None:
        route = resolve_docs("triage", None, [], request_classified=True)

        self.assertNotIn(ROUTE_DOCS_READ_GATE, route["gates"])
        self.assertNotIn(TEST_GATE, route["gates"])
        self.assertNotIn(MULTI_AGENT_GATE, route["gates"])

    def test_workflow_setup_reads_route_docs_before_repair(self) -> None:
        route = resolve_docs("workflow-setup", None, ["structure"], request_classified=True)

        self.assertIn(ROUTE_DOCS_READ_GATE, route["gates"])
        self.assertLess(
            route["gates"].index(ROUTE_DOCS_READ_GATE),
            route["gates"].index(AMBIGUITY_GATE),
        )
        self.assertLess(
            route["gates"].index(ROUTE_DOCS_READ_GATE),
            route["gates"].index("install or repair"),
        )

    def test_docs_route_reads_route_docs_before_edit(self) -> None:
        route = resolve_docs("docs", None, ["structure"], request_classified=True)

        self.assertIn(ROUTE_DOCS_READ_GATE, route["gates"])
        self.assertLess(route["gates"].index(ROUTE_DOCS_READ_GATE), route["gates"].index("edit"))

    def test_finish_policy_rejects_empty_gate_phrases(self) -> None:
        failures = validate_gate_evidence(
            {
                ROUTE_DOCS_READ_GATE: "done",
                AMBIGUITY_GATE: "done",
                ALIGNMENT_BRIEF_GATE: "done",
                DOCUMENTATION_GATE: "done",
                TEST_GATE: "done",
                BOUNDARY_PLAN_GATE: "done",
                MULTI_AGENT_GATE: "done",
                SIDE_EFFECT_AUDIT_GATE: "done",
            },
            [
                ROUTE_DOCS_READ_GATE,
                AMBIGUITY_GATE,
                ALIGNMENT_BRIEF_GATE,
                DOCUMENTATION_GATE,
                TEST_GATE,
                BOUNDARY_PLAN_GATE,
                MULTI_AGENT_GATE,
                SIDE_EFFECT_AUDIT_GATE,
            ],
        )

        self.assertEqual(8, len(failures))

    def test_alignment_evidence_requires_user_visible_checkpoint(self) -> None:
        failures = validate_gate_evidence(
            {
                ALIGNMENT_BRIEF_GATE: (
                    "same understanding: explicit goal captured; possible differences: uncertain scope; "
                    "unsupported assumptions: default MVP unless blocker question changes it"
                )
            },
            [ALIGNMENT_BRIEF_GATE],
        )

        self.assertTrue(any("user-visible checkpoint" in failure for failure in failures))

    def test_finish_policy_accepts_specific_evidence(self) -> None:
        failures = validate_gate_evidence(
            {
                ROUTE_DOCS_READ_GATE: (
                    "read routed docs before code: AGENTS.md, index.md, "
                    "common/agent-operating-skill.md"
                ),
                AMBIGUITY_GATE: "no blockers; safe assumption recorded",
                ALIGNMENT_BRIEF_GATE: (
                    "same understanding: explicit goal captured; possible differences: uncertain scope; "
                    "unsupported assumptions: default MVP unless blocker question changes it; "
                    "user-visible checkpoint told the user before edits"
                ),
                DOCUMENTATION_GATE: "updated workflows/README.md",
                TEST_GATE: "unittest tests/test_workflow_routing.py passed",
                BOUNDARY_PLAN_GATE: "existing workflow gate policy boundary; verification via unittest",
                MULTI_AGENT_GATE: "no subagent split: small single-file policy change with same-file scope",
                SIDE_EFFECT_AUDIT_GATE: "final diff checked; no unexpected generated files or lockfile changes",
            },
            [
                ROUTE_DOCS_READ_GATE,
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
