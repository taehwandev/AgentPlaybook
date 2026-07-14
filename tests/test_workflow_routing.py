from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_finish_common import requires_retrospective
from agent_finish_gate_core_validators import validate_route_docs_application_fields
from agent_finish_gate_policy import (
    PLATFORM_SELECTION_GATE,
    PRD_DRAFT_GATE,
    REVIEW_READINESS_GATE,
    VALIDATED_GATES,
    validate_gate_evidence,
)
from agent_finish_check_steps import (
    check_request_intake,
    read_route_docs_receipt_for_preflight,
    validate_grill_me_skill_evidence,
    validate_route_docs_manifest_evidence,
)
from agent_gate_evidence import (
    gate_evidence_path_for_preflight,
    merge_gate_evidence_from_ledger,
    record_gate_evidence,
    record_many_gate_evidence,
    reset_gate_evidence_ledger,
    synthesize_gate_evidence,
)
from agent_delegation_plan import validate_delegation_plan_evidence
from agent_global_lessons import lesson_summary, write_retrospective_candidate
from agent_hook_runtime import hook_failure_policy
from agent_preflight_runtime import (
    AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES as PREFLIGHT_AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES,
    _claude_spill_warnings,
)
from agent_review_hook import review_hook, review_vibeguard_command, workflow_validate_failure_detail
from agent_review_structure import structure_review
from agent_vibeguard_cache import cached_vibeguard
from agent_route_docs import (
    preflight_evidence_sha256,
    receipt_path_for_evidence,
    route_docs_to_read,
    route_fingerprint,
)
from support.agy_setup import AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES, _agy_runtime_bridge_block
from support.claude_setup import _CLASSIFICATION_EVIDENCE, _merge_claude_user_prompt_submit
from support.permission_entries import agy_permission_entries, claude_permission_entries, codex_prefix_rule_entries
from support.runtime_bridge import (
    CODEX_DISPATCH_BRIDGE_PHRASE,
    RUNTIME_BRIDGE_GRAPH_PHRASES,
    runtime_bridge_block,
    runtime_bridge_required_phrases,
)
from support.stable_launcher import stable_launcher_path
from workflow_catalog import COMMANDS, CONCERNS, SPILL_ACTION_LABELS
from workflow_gate_policy import (
    AGENTIC_RUN_STATE_GATE,
    AMBIGUITY_GATE,
    ALIGNMENT_BRIEF_GATE,
    BOUNDARY_PLAN_GATE,
    CYCLE_CONTRACT_GATE,
    DOCUMENTATION_IMPACT_GATE,
    DOCUMENTATION_GATE,
    MULTI_AGENT_GATE,
    PRODUCT_REENTRY_GATE,
    PRODUCT_REENTRY_COMMANDS,
    ROUTE_DOCS_READ_GATE,
    SIDE_EFFECT_AUDIT_GATE,
    SOURCE_DOCS_GATE,
    TEST_GATE,
    ALIGNMENT_BRIEF_COMMANDS,
    WORK_PRODUCING_COMMANDS,
)
from workflow_request import infer_concerns_from_request
from workflow_request import classify_request
from workflow_request import classified_route_block_reason
from workflow_request import route_block_reason
from workflow_dispatch import build_dispatch_manifest, execute_dispatch_manifest
from workflow_dispatch_profiles import profile_for_work_kind, select_work_kind
from workflow_doc_surfaces import (
    extract_request_surface_paths,
    git_status_surface_paths,
    infer_surface_docs,
    load_doc_surface_rules,
    surface_rule_doc_refs,
)
from workflow_doc_graph import (
    clear_doc_graph_cache,
    expand_doc_matches,
    graph_required_docs,
)
from workflow_parallel_validate import validate_parallel_execution_plan
from workflow_route import resolve_docs
from workflow_search import search_docs, search_docs_outcome
from workflow_skill_paths import canonical_doc_path
from workflow_spill import spill_tool_label, validate_spill_label_contracts
from workflow import build_parser, print_dispatch
from workflow_validate import STRICT_CARD_REQUIRED_HEADINGS, markdown_files_to_validate


def route_doc(path: str) -> str:
    return canonical_doc_path(path)


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
        self.assertIn("common/skills/testing/SKILL.md", CONCERNS["testing"])
        self.assertIn("common/skills/scenario-driven-testing/SKILL.md", CONCERNS["testing"])
        self.assertIn("common/skills/verification-policy/SKILL.md", CONCERNS["testing"])
        self.assertIn("definition-of-done", CONCERNS)
        self.assertIn("common/skills/definition-of-done/SKILL.md", CONCERNS["definition-of-done"])

    def test_workflow_validate_ignores_generated_markdown_caches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            cache_dir = root / ".pytest_cache"
            graphify_dir = root / "graphify-out"
            docs_dir.mkdir()
            cache_dir.mkdir()
            graphify_dir.mkdir()
            valid_doc = docs_dir / "guide.md"
            valid_doc.write_text(
                "---\nkeyflow_id: test\nstatus: stable\ntype: human-reviewed\n---\n# Guide\n",
                encoding="utf-8",
            )
            (cache_dir / "README.md").write_text("# Cache\n", encoding="utf-8")
            (graphify_dir / "GRAPH_REPORT.md").write_text("# Generated graph report\n", encoding="utf-8")

            self.assertEqual([valid_doc], markdown_files_to_validate(root))

    def test_lifecycle_alias_commands_are_registered(self) -> None:
        for command in ("spec", "plan", "build", "test", "webperf", "code-simplify", "ship"):
            with self.subTest(command=command):
                self.assertIn(command, COMMANDS)
                route = resolve_docs(command, None, [], request_classified=True)

                self.assertIn("request intake", route["gates"])
                self.assertIn(ROUTE_DOCS_READ_GATE, route["gates"])

        self.assertIn(route_doc("common/skills/incremental-implementation/SKILL.md"), resolve_docs("build", None, [], request_classified=True)["docs"])
        self.assertIn(route_doc("common/skills/performance-verification/SKILL.md"), resolve_docs("webperf", None, [], request_classified=True)["docs"])
        self.assertIn(route_doc("common/skills/web-performance-verification/SKILL.md"), resolve_docs("webperf", None, [], request_classified=True)["docs"])
        self.assertIn(route_doc("common/skills/ci-cd-automation/SKILL.md"), resolve_docs("ship", None, [], request_classified=True)["docs"])

        test_route = resolve_docs("test", None, [], request_classified=True)
        self.assertIn(route_doc("common/skills/scenario-driven-testing/SKILL.md"), test_route["docs"])

        webperf_route = resolve_docs("webperf", None, [], request_classified=True)
        self.assertLess(webperf_route["gates"].index(ROUTE_DOCS_READ_GATE), webperf_route["gates"].index("baseline"))
        self.assertLess(webperf_route["gates"].index(ALIGNMENT_BRIEF_GATE), webperf_route["gates"].index("baseline"))

        spec_route = resolve_docs("spec", None, [], request_classified=True)
        self.assertLess(spec_route["gates"].index(ROUTE_DOCS_READ_GATE), spec_route["gates"].index("local product docs"))
        self.assertLess(spec_route["gates"].index(ROUTE_DOCS_READ_GATE), spec_route["gates"].index("ambiguity check"))

    def test_agent_skills_gap_concerns_are_registered(self) -> None:
        expected = {
            "skill-card": "common/skills/agent-skill-card-anatomy/SKILL.md",
            "source-driven": "common/skills/source-driven-development/SKILL.md",
            "doubt-driven": "common/skills/doubt-driven-development/SKILL.md",
            "incremental": "common/skills/incremental-implementation/SKILL.md",
            "deprecation": "common/skills/deprecation-migration/SKILL.md",
            "ci": "common/skills/ci-cd-automation/SKILL.md",
            "webperf": "common/skills/performance-verification/SKILL.md",
            "browser-testing": "common/skills/browser-runtime-testing/SKILL.md",
            "wiki": "common/skills/llm-wiki-documentation/SKILL.md",
            "commit": "common/skills/commit-workflow/SKILL.md",
            "branch": "common/skills/branch-strategy/SKILL.md",
            "push": "common/skills/commit-workflow/SKILL.md",
            "pull-request": "common/skills/branch-strategy/SKILL.md",
            "tag": "common/skills/release-deployment/SKILL.md",
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
        self.assertIn("common/skills/local-tools/SKILL.md", CONCERNS["metering"])
        self.assertIn("docs/skills/agent-runtime-integration/SKILL.md", CONCERNS["local-tools"])
        self.assertIn("common/skills/local-tools/SKILL.md", CONCERNS["usage"])
        self.assertIn("common/skills/design-system/SKILL.md", CONCERNS["tokens"])
        self.assertNotIn("common/skills/local-tools/SKILL.md", CONCERNS["tokens"])

    def test_web_deployment_versioning_routes_with_release_and_shipping(self) -> None:
        doc = "common/skills/web-deployment-versioning/SKILL.md"

        self.assertIn(doc, CONCERNS["release"])
        self.assertIn(doc, CONCERNS["shipping"])
        self.assertIn("workflows/skills/release-readiness/SKILL.md", CONCERNS["release"])
        self.assertIn(route_doc(doc), resolve_docs("docs", "web", ["release"], request_classified=True)["docs"])
        self.assertIn(route_doc(doc), resolve_docs("ship", "web", ["shipping"], request_classified=True)["docs"])

        examples = (
            "Define web deployment versioning for every main merge",
            "Should web deploys bump SemVer or use deployment ids?",
            "웹 배포 버전 체계를 정리해줘",
        )
        for request in examples:
            with self.subTest(request=request):
                self.assertIn("release", infer_concerns_from_request(request))

    def test_release_route_requires_versioning_skill_doc(self) -> None:
        route = resolve_docs("release", None, [], request_classified=True)

        self.assertIn(route_doc("workflows/skills/release-readiness/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/release-deployment/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/release-versioning/SKILL.md"), route["required_docs"])
        self.assertNotIn(route_doc("common/skills/release-versioning/SKILL.md"), route["reference_docs"])

    def test_tag_concern_requires_release_and_git_safety_skill_docs(self) -> None:
        expected_docs = (
            "common/skills/commit-workflow/SKILL.md",
            "common/skills/worktree-hygiene/SKILL.md",
            "workflows/skills/release-readiness/SKILL.md",
            "common/skills/release-deployment/SKILL.md",
            "common/skills/release-versioning/SKILL.md",
        )

        for doc in expected_docs:
            with self.subTest(doc=doc):
                self.assertIn(doc, CONCERNS["tag"])

        route = resolve_docs("release", None, ["tag"], request_classified=True)
        for doc in expected_docs:
            with self.subTest(required_doc=doc):
                self.assertIn(route_doc(doc), route["required_docs"])

    def test_release_versioning_forbids_four_digit_year_calver_tags(self) -> None:
        guidance = (ROOT / "common/skills/release-versioning/references/current-guidance.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("weekly CalVer `YY.WW.N`", guidance)
        self.assertIn("four-digit years", guidance)
        self.assertIn("2026.27.1", guidance)
        self.assertIn("starts at `1`", guidance)

    def test_credential_broker_concern_routes_to_product_pattern(self) -> None:
        doc = "product-patterns/skills/agent-credential-broker-ideation/SKILL.md"
        for concern in (
            "credential-broker",
            "agent-credentials",
            "brokered-credentials",
            "capability-token",
            "egress-control",
        ):
            with self.subTest(concern=concern):
                self.assertIn(concern, CONCERNS)
                self.assertIn(doc, CONCERNS[concern])

        examples = (
            "Compare credential broker patterns for an AI coding agent",
            "Design brokered credentials and capability token access for agents",
            "에이전트 자격 증명 브로커 아이디에이션을 정리해줘",
        )
        for request in examples:
            with self.subTest(request=request):
                self.assertIn("credential-broker", infer_concerns_from_request(request))

        route = resolve_docs("planning", None, ["credential-broker"], request_classified=True)
        self.assertIn(route_doc(doc), route["docs"])

    def test_number_unit_display_concerns_route_to_accessibility_i18n(self) -> None:
        for concern in (
            "i18n",
            "localization",
            "number-format",
            "number",
            "numbers",
            "numeric",
            "unit",
            "units",
            "measurement",
            "measurements",
            "currency",
            "display-value",
            "display-values",
        ):
            with self.subTest(concern=concern):
                self.assertIn(concern, CONCERNS)
                self.assertIn("common/skills/accessibility-i18n/SKILL.md", CONCERNS[concern])

        examples = (
            "Fix visible number and unit display in metric cards",
            "Format storage size units and duration labels",
            "숫자 표기와 단위를 화면 표시 기준으로 처리해줘",
        )

        for request in examples:
            with self.subTest(request=request):
                concerns = infer_concerns_from_request(request)
                self.assertIn("accessibility", concerns)

        route = resolve_docs("docs", None, ["units"], request_classified=True)
        self.assertIn(route_doc("common/skills/accessibility-i18n/SKILL.md"), route["docs"])

    def test_scenario_testing_requests_infer_testing_concern(self) -> None:
        examples = (
            "Write scenario-driven tests for the checkout user flow",
            "Add QA scenarios for UI success and failure states",
            "사용자 흐름과 예외 처리를 시나리오 테스트로 정리해줘",
        )

        for request in examples:
            with self.subTest(request=request):
                self.assertIn("testing", infer_concerns_from_request(request))

    def test_spill_request_infers_metering_concern(self) -> None:
        concerns = infer_concerns_from_request("Preserve Spill workflow label bridge data")

        self.assertIn("metering", concerns)

    def test_natural_code_cleanup_request_routes_to_code_simplify(self) -> None:
        classification = classify_request("코드 정리해줘")

        self.assertEqual("clear-scoped", classification["clarity"])
        self.assertEqual("code-simplify", classification["recommended_route"])
        self.assertFalse(classification["grill_me"])

    def test_natural_change_review_request_routes_to_review(self) -> None:
        for request in ("변경사항 검토하고 확인해줘", "이 작업 검토하고 확인해줘"):
            with self.subTest(request=request):
                classification = classify_request(request)

                self.assertEqual("clear-scoped", classification["clarity"])
                self.assertEqual("review", classification["recommended_route"])
                self.assertFalse(classification["grill_me"])

    def test_android_screen_request_routes_to_feature(self) -> None:
        classification = classify_request(
            "안드로이드 작업에서 첫 화면에서는 전체 목록이, 두번째 화면에서는 즐겨찾기가 있는 화면을 구성해줘"
        )

        self.assertEqual("clear-scoped", classification["clarity"])
        self.assertEqual("feature", classification["recommended_route"])
        self.assertFalse(classification["grill_me"])

    def test_natural_language_doc_routing_request_routes_to_workflow_setup(self) -> None:
        classification = classify_request("훅은 보완이고 자연어 검색 가능한 문서 라우팅을 강화해줘")

        self.assertEqual("clear-scoped", classification["clarity"])
        self.assertEqual("workflow-setup", classification["recommended_route"])
        self.assertFalse(classification["grill_me"])

    def test_classification_includes_runtime_neutral_model_selection(self) -> None:
        quick = classify_request("`scripts/workflow_request.py:10` 확인해줘")
        standard = classify_request("기획변경 때 문서 정리가 누락되는 걸 막아줘")
        deep = classify_request("프로필 설정 기능을 구현해줘")

        self.assertEqual("quick", quick["effort"])
        self.assertEqual("fast", quick["model_tier"])
        self.assertEqual("gpt-5.6-luna", quick["model_selection"]["codex"])

        self.assertEqual("standard", standard["effort"])
        self.assertEqual("balanced", standard["model_tier"])
        self.assertEqual("gpt-5.6-terra", standard["model_selection"]["codex"])

        self.assertEqual("deep", deep["effort"])
        self.assertEqual("frontier", deep["model_tier"])
        self.assertEqual("gpt-5.6-sol", deep["model_selection"]["codex"])
        self.assertEqual(
            "codex-only-or-runtime-equivalent",
            deep["model_selection"]["runtime_mapping"],
        )
        self.assertEqual("task-or-agent-boundary", deep["model_selection"]["switching_boundary"])
        self.assertIn(
            "Use Codex model ids only on Codex",
            deep["model_selection"]["runtime_policy"],
        )

    def test_dispatch_profiles_match_stage_policy(self) -> None:
        expected = {
            "prd_design": ("gpt-5.6-sol", "high"),
            "research": ("gpt-5.6-terra", "low"),
            "analysis": ("gpt-5.6-terra", "medium"),
            "implementation": ("gpt-5.6-terra", "medium"),
            "complex_implementation": ("gpt-5.6-sol", "high"),
            "repetitive": ("gpt-5.6-luna", "low"),
            "final_review": ("gpt-5.6-sol", "xhigh"),
        }

        for work_kind, (model, effort) in expected.items():
            with self.subTest(work_kind=work_kind):
                profile = profile_for_work_kind(work_kind)
                self.assertEqual(model, profile["codex_model"])
                self.assertEqual(effort, profile["reasoning_effort"])

    def test_dispatch_keeps_normal_implementation_on_terra_medium(self) -> None:
        manifest = build_dispatch_manifest(
            "feature",
            "기획변경 때 문서 정리가 누락되는 걸 막아줘",
            ROOT,
        )

        profile = manifest["work_profile"]
        self.assertEqual("implementation", profile["work_kind"])
        self.assertEqual("gpt-5.6-terra", profile["codex_model"])
        self.assertEqual("medium", profile["reasoning_effort"])
        self.assertIn("--model", manifest["codex_exec_argv"])
        self.assertIn('model_reasoning_effort="medium"', manifest["codex_exec_argv"])
        self.assertEqual("workspace-write", manifest["sandbox_mode"])

    def test_dispatch_auto_selects_stage_profiles(self) -> None:
        cases = {
            "prd": ("prd_design", "high"),
            "plan": ("research", "low"),
            "task": ("analysis", "medium"),
            "feature": ("implementation", "medium"),
            "review": ("final_review", "xhigh"),
        }

        for command, (work_kind, effort) in cases.items():
            with self.subTest(command=command):
                manifest = build_dispatch_manifest(
                    command,
                    "기획변경 때 문서 정리가 누락되는 걸 막아줘",
                    ROOT,
                )
                profile = manifest["work_profile"]
                self.assertEqual(work_kind, profile["work_kind"])
                self.assertEqual(effort, profile["reasoning_effort"])

    def test_dispatch_auto_promotes_deep_implementation_to_sol_high(self) -> None:
        work_kind, reason = select_work_kind("feature", {"effort": "deep"}, "auto")
        profile = profile_for_work_kind(work_kind)

        self.assertEqual("complex_implementation", profile["work_kind"])
        self.assertEqual("gpt-5.6-sol", profile["codex_model"])
        self.assertEqual("high", profile["reasoning_effort"])
        self.assertEqual("deep effort is explicit complexity evidence", reason)

    def test_dispatch_reserves_luna_for_quick_repetition(self) -> None:
        quick = {"effort": "quick"}

        self.assertEqual(
            ("repetitive", "quick non-authoring test route selects the read-only Luna profile"),
            select_work_kind("test", quick, "auto"),
        )
        self.assertEqual(
            ("implementation", "normal implementation defaults to Terra medium"),
            select_work_kind("feature", quick, "auto"),
        )

    def test_dispatch_keeps_code_authoring_tests_on_terra(self) -> None:
        manifest = build_dispatch_manifest(
            "test",
            "Add a regression test for `scripts/workflow_dispatch.py:10`.",
            ROOT,
        )

        self.assertEqual("implementation", manifest["work_profile"]["work_kind"])
        self.assertEqual("gpt-5.6-terra", manifest["work_profile"]["codex_model"])
        self.assertEqual("workspace-write", manifest["sandbox_mode"])

    def test_classification_keeps_code_authoring_above_luna(self) -> None:
        classification = classify_request("Add a regression test for `scripts/workflow_dispatch.py:10`.")

        self.assertEqual("quick", classification["effort"])
        self.assertEqual("balanced", classification["model_tier"])
        self.assertEqual("gpt-5.6-terra", classification["model_selection"]["codex"])

    def test_dispatch_makes_luna_repetition_read_only_and_non_authoring(self) -> None:
        manifest = build_dispatch_manifest(
            "test",
            "Run the focused tests for `scripts/workflow_dispatch.py:10`.",
            ROOT,
        )

        self.assertEqual("repetitive", manifest["work_profile"]["work_kind"])
        self.assertEqual("gpt-5.6-luna", manifest["work_profile"]["codex_model"])
        self.assertEqual("read-only", manifest["sandbox_mode"])
        self.assertEqual("read-only non-authoring", manifest["authoring_policy"])
        self.assertIn("Do not modify files, write code, generate patches, or create tests.", manifest["codex_exec_argv"][-1])

    def test_dispatch_rejects_luna_for_explicit_code_authoring(self) -> None:
        with self.assertRaisesRegex(ValueError, "Luna cannot write or modify code"):
            select_work_kind(
                "feature",
                {"effort": "quick", "request": "Implement the requested code change."},
                "repetitive",
            )

    def test_dispatch_promotes_deep_work_to_sol_high(self) -> None:
        manifest = build_dispatch_manifest(
            "task",
            "기획변경 때 문서 정리가 누락되는 걸 막아줘",
            ROOT,
            work_kind="complex_implementation",
            complexity_evidence="local inspection confirmed cross-module migration and repeated verification failures",
        )

        profile = manifest["work_profile"]
        self.assertEqual("complex_implementation", profile["work_kind"])
        self.assertEqual("gpt-5.6-sol", profile["codex_model"])
        self.assertEqual("high", profile["reasoning_effort"])

    def test_dispatch_rejects_unexplained_complex_implementation(self) -> None:
        with self.assertRaisesRegex(ValueError, "Complex implementation requires"):
            build_dispatch_manifest(
                "task",
                "기획변경 때 문서 정리가 누락되는 걸 막아줘",
                ROOT,
                work_kind="complex_implementation",
            )

    def test_dispatch_cli_outputs_a_nonexecuting_terra_handoff(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "dispatch",
                "task",
                "--request",
                "기획변경 때 문서 정리가 누락되는 걸 막아줘",
                "--project",
                str(ROOT),
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        manifest = json.loads(completed.stdout)
        self.assertEqual("gpt-5.6-terra", manifest["work_profile"]["codex_model"])
        self.assertEqual("medium", manifest["work_profile"]["reasoning_effort"])
        self.assertIn("inspectable by default", manifest["execution_policy"])

    def test_dispatch_executor_runs_selected_argv(self) -> None:
        manifest = build_dispatch_manifest(
            "feature",
            "기획변경 때 문서 정리가 누락되는 걸 막아줘",
            ROOT,
        )
        received: list[list[str]] = []

        def runner(argv: list[str]) -> int:
            received.append(argv)
            return 17

        self.assertEqual(17, execute_dispatch_manifest(manifest, runner=runner))
        self.assertEqual([manifest["codex_exec_argv"]], received)

    def test_dispatch_execute_cli_uses_executor(self) -> None:
        args = build_parser().parse_args(
            [
                "dispatch",
                "feature",
                "--request",
                "기획변경 때 문서 정리가 누락되는 걸 막아줘",
                "--project",
                str(ROOT),
                "--execute",
            ]
        )

        with patch("workflow.execute_dispatch_manifest", return_value=23) as execute:
            self.assertEqual(23, print_dispatch(args))

        execute.assert_called_once()

    def test_dispatch_handoff_state_preserves_parent_evidence_paths(self) -> None:
        manifest = build_dispatch_manifest(
            "feature",
            "기획변경 때 문서 정리가 누락되는 걸 막아줘",
            ROOT,
        )
        handoff_state = manifest["handoff_state"]
        prompt = manifest["codex_exec_argv"][-1]

        self.assertTrue(str(handoff_state["preflight_evidence"]).endswith("preflight.json"))
        self.assertTrue(str(handoff_state["docs_read_receipt"]).endswith("route-docs-read.json"))
        self.assertTrue(str(handoff_state["gate_ledger"]).endswith("gate-evidence.json"))
        self.assertIn("Parent docs-read receipt", prompt)
        self.assertIn("Do not overwrite parent receipts", prompt)

    def test_dispatch_spill_label_contract_is_preserved(self) -> None:
        self.assertEqual(("workflow_setup", "plan"), SPILL_ACTION_LABELS["dispatch"])
        self.assertEqual([], validate_spill_label_contracts(set(COMMANDS)))

    def test_runtime_dispatch_paths_promote_runtime_guidance(self) -> None:
        route = resolve_docs(
            "workflow-setup",
            None,
            [],
            request_classified=True,
            surface_paths=["scripts/workflow_spill.py"],
        )

        for doc in (
            "docs/skills/agent-runtime-integration/SKILL.md",
            "workflows/skills/agent-handoff-continuation/SKILL.md",
            "common/skills/local-tools/SKILL.md",
        ):
            self.assertIn(route_doc(doc), route["required_docs"])

    def test_claude_user_prompt_hook_requires_classification_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "settings.json"
            old_command = (
                "SPILL_AI_TOOL=claude python3 '/tmp/AgentPlaybook/scripts/workflow.py' "
                "route triage --request-classified"
            )
            target.write_text(json.dumps({
                "hooks": {
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [{"type": "command", "command": old_command, "timeout": 5}],
                        }
                    ]
                }
            }))
            new_command = (
                f"AGENTPLAYBOOK_HOOK_SOFT_FAIL=1 SPILL_AI_TOOL=claude '{stable_launcher_path()}' workflow "
                "route triage --request-classified --classification-evidence "
                f"'{_CLASSIFICATION_EVIDENCE}'"
            )

            status = _merge_claude_user_prompt_submit(target, new_command, dry_run=False)
            config = json.loads(target.read_text())
            commands = [
                hook["command"]
                for group in config["hooks"]["UserPromptSubmit"]
                for hook in group["hooks"]
            ]

        self.assertEqual("installed", status)
        self.assertNotIn(old_command, commands)
        self.assertIn(new_command, commands)

    def test_preflight_warns_for_claude_hook_without_classification_evidence(self) -> None:
        config = {
            "hooks": {
                "UserPromptSubmit": [
                    {
                        "hooks": [
                            {
                                "command": (
                                    "SPILL_AI_TOOL=claude python3 "
                                    "'/tmp/AgentPlaybook/scripts/workflow.py' "
                                    "route triage --request-classified"
                                )
                            }
                        ]
                    }
                ]
            },
            "env": {"SPILL_AI_TOOL": "claude"},
        }

        warnings = _claude_spill_warnings(config, Path("/tmp/AgentPlaybook"))

        self.assertTrue(any("--classification-evidence" in warning for warning in warnings))

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
            ("Apply OpenWiki-style living wiki docs", "wiki"),
            ("Generate source-grounded documentation from this codebase", "wiki"),
            ("코드베이스 위키와 자동 문서 갱신 방식을 정리해줘", "wiki"),
            ("Create commit rules for feature branches and PRs", "commit"),
            ("Create commit rules for feature branches and PRs", "branch"),
            ("Use git username/work-unit/description for branch names", "branch"),
            ("브랜치 전략을 git username 작업단위 내용으로 정리", "branch"),
            ("Automate git push only after safety checks", "push"),
            ("Open a draft PR from the work branch", "pull-request"),
            ("Release by pushing a verified tag", "tag"),
            ("태그 따고 푸쉬해줘", "tag"),
            ("태그 따고 푸쉬해줘", "push"),
        )

        for request, concern in examples:
            with self.subTest(request=request):
                self.assertIn(concern, infer_concerns_from_request(request))

    def test_commit_request_uses_lightweight_commit_route(self) -> None:
        classification = classify_request("웹 코드 커밋 안한거 분리해서 커밋해줘")

        self.assertEqual("commit", classification["recommended_route"])
        self.assertEqual("quick", classification["effort"])
        self.assertFalse(classification["grill_me"])

        self.assertIn("commit", COMMANDS)
        self.assertIn("git_commit", COMMANDS)

        route = resolve_docs("git_commit", None, [], request_classified=True)

        self.assertEqual(
            [ROUTE_DOCS_READ_GATE, "review hook", "commit readiness"],
            [gate for gate in route["gates"] if gate != "request intake"],
        )
        self.assertNotIn(AMBIGUITY_GATE, route["gates"])
        self.assertNotIn(ALIGNMENT_BRIEF_GATE, route["gates"])
        self.assertNotIn(CYCLE_CONTRACT_GATE, route["gates"])
        self.assertNotIn(BOUNDARY_PLAN_GATE, route["gates"])
        self.assertNotIn(MULTI_AGENT_GATE, route["gates"])
        self.assertIn(route_doc("workflows/skills/review-and-commit/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/commit-workflow/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/code-review/SKILL.md"), route["reference_docs"])
        self.assertIn(route_doc("common/skills/worktree-hygiene/SKILL.md"), route["reference_docs"])

    def test_branch_strategy_routes_for_branch_naming(self) -> None:
        concerns = infer_concerns_from_request(
            "Use git username/work-unit/description for branch names"
        )

        self.assertIn("branch", concerns)

        route = resolve_docs("docs", None, ["branch"], request_classified=True)

        self.assertIn(route_doc("common/skills/branch-strategy/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/worktree-hygiene/SKILL.md"), route["required_docs"])

    def test_preflight_rejects_invalid_concern_like_workflow_route_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "agent-preflight.py"),
                    "--project",
                    str(project),
                    "--rules",
                    str(ROOT),
                    "--command",
                    "bugfix",
                    "--concern",
                    "not-a-real-concern",
                    "--request-classified",
                    "--classification-evidence",
                    "clear-scoped actionable request: verify preflight parser validation",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(2, result.returncode)
        self.assertIn("invalid choice", result.stderr)

    def test_git_commit_route_accepts_commit_classification_evidence(self) -> None:
        evidence = (
            "User asked to split all uncommitted web code into commits. "
            "Target repo is known and current task is local commit creation."
        )

        self.assertIsNone(classified_route_block_reason("git_commit", evidence))

    def test_finish_request_intake_uses_commit_evidence_policy(self) -> None:
        evidence = (
            "User asked to split all uncommitted web code into commits. "
            "Target repo is known and current task is local commit creation."
        )
        route = {
            "command": "git_commit",
            "request_classified": True,
        }
        failures: list[str] = []
        gate_signals: list[dict[str, str]] = []
        missed_gates: list[str] = []

        check_request_intake(
            route,
            {"request_classified": True, "classification_evidence": evidence},
            {},
            {},
            gate_signals,
            missed_gates,
            failures,
        )

        self.assertEqual([], failures)
        self.assertEqual([], missed_gates)

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
        self.assertIn(route_doc("common/skills/human-authored-writing/SKILL.md"), route["docs"])
        self.assertIn(route_doc("common/skills/writing-workspace/SKILL.md"), route["docs"])

    def test_ambiguous_writing_style_rewrite_requires_triage(self) -> None:
        request = (
            "# AgentPlaybook: AI 에이전트의 작업 습관을 프로젝트 밖에 저장하기 "
            "이거 작성 다시하자. 나는 ~했다. 뭐뭐다. 이다. "
            "이런 투로 쓰는데 존대라서 이런건 어떻게 내 스타일로 쓰도록 가이드하지?"
        )

        classification = classify_request(request)

        self.assertIn("writing", infer_concerns_from_request(request))
        self.assertEqual("vague-action", classification["clarity"])
        self.assertTrue(classification["grill_me"])
        self.assertEqual("triage", classification["recommended_route"])
        self.assertEqual("clarify_first", classification["response_mode"])

    def test_android_performance_route_loads_external_skill_manifest(self) -> None:
        route = resolve_docs(
            "workflow-setup",
            "android",
            ["performance"],
            request_classified=True,
        )

        self.assertIn(route_doc("common/skills/performance-verification/SKILL.md"), route["docs"])
        self.assertIn(route_doc("platforms/android/skills/android-compose-ui/SKILL.md"), route["docs"])
        self.assertIn(route_doc("platforms/android/skills/android-review/SKILL.md"), route["docs"])
        self.assertIn(route_doc("platforms/android/skills/android-external-skill-source-coverage/SKILL.md"), route["docs"])

    def test_android_platform_surfaces_load_external_skill_manifest(self) -> None:
        for concern in ("architecture", "security", "testing", "module", "dependency", "migration", "devtools", "skills", "skill"):
            with self.subTest(concern=concern):
                route = resolve_docs(
                    "workflow-setup",
                    "android",
                    [concern],
                    request_classified=True,
                )

                self.assertIn(route_doc("platforms/android/skills/android-external-skill-source-coverage/SKILL.md"), route["docs"])
                self.assertIn(route_doc("platforms/android/skills/source-coverage/SKILL.md"), route["docs"])

    def test_android_persistence_route_loads_datastore_reference(self) -> None:
        for concern in ("persistence", "cache"):
            with self.subTest(concern=concern):
                route = resolve_docs(
                    "feature",
                    "android",
                    [concern],
                    request_classified=True,
                )

                self.assertIn(route_doc("platforms/android/skills/android-state-data/SKILL.md"), route["docs"])
                self.assertIn("platforms/android/skills/android-state-data/references/android-datastore.md", route["docs"])

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
            self.assertEqual(
                "run_actionable_retrospective_then_retry_same_scope",
                lesson["next_action"],
            )
            self.assertEqual(
                "immediate_correction_plan",
                lesson["required_retrospective_output"],
            )
            self.assertEqual(
                "second_attempt_cites_retrospective_plan_and_resumes_first_missed_gate",
                lesson["retry_rule"],
            )
            self.assertEqual(
                "cite_or_apply_retrospective_correction_plan",
                lesson["second_attempt_requirement"],
            )
            for private_key in ("project", "path", "prompt", "command", "diff", "repo", "branch"):
                self.assertNotIn(private_key, lesson)

            summary = lesson_summary()
            self.assertEqual(1, summary["candidate_count"])

    def test_hook_failure_policy_requires_retrospective_before_retry(self) -> None:
        policy, details = hook_failure_policy(success=False, retry_attempt=0)

        self.assertEqual("retrospective_then_retry_once", policy["next_action"])
        self.assertEqual("actionable_retrospective", policy["recovery_required"])
        joined_details = " ".join(details)
        self.assertIn("actionable retrospective", joined_details)
        self.assertIn("immediate correction plan", joined_details)
        self.assertIn("--retry-attempt 1", joined_details)
        self.assertIn("cite or apply", joined_details)

    def test_hook_failure_policy_stops_after_retrospective_retry_fails(self) -> None:
        policy, details = hook_failure_policy(success=False, retry_attempt=1)

        self.assertEqual("stop_after_retrospective_retry_failed", policy["next_action"])
        self.assertEqual("promote_or_handoff_lesson", policy["recovery_required"])
        joined_details = " ".join(details)
        self.assertIn("retry limit reached", joined_details)
        self.assertIn("promote the retrospective lesson", joined_details)

    def test_finish_final_check_failure_requires_retrospective_lesson(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["AGENTPLAYBOOK_STATE_HOME"] = temp_dir

            retrospective_required = requires_retrospective(
                missed_gates=[],
                gate_policy_failures=[],
                finish_failures=["workflow validate failed"],
            )
            result = write_retrospective_candidate(
                {
                    "retrospective_required": retrospective_required,
                    "missed_gates": [],
                    "gate_signals": [{"gate": "workflow validate", "signal": "FAIL"}],
                }
            )

            self.assertTrue(retrospective_required)
            self.assertTrue(result["created"])
            lesson_path = Path(temp_dir) / result["relative_path"]
            lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
            self.assertEqual("finish_gate_failure", lesson["failure_type"])
            self.assertEqual("finish_failed_before_completion", lesson["root_cause"])
            self.assertEqual(
                "run_actionable_retrospective_then_retry_same_scope",
                lesson["next_action"],
            )

    def test_setup_permissions_include_new_workflow_helpers(self) -> None:
        entries = "\n".join(codex_prefix_rule_entries(ROOT / "scripts"))

        self.assertIn("workflow_gate_policy.py", entries)
        self.assertIn("workflow_concern_docs.py", entries)
        self.assertIn("agent-docs-read.py", entries)
        self.assertIn("agent_delegation_plan.py", entries)
        self.assertIn("agent_finish_gate_policy.py", entries)
        self.assertIn("agent_gate_evidence.py", entries)
        self.assertIn("agent_finish_common.py", entries)
        self.assertIn("agent_finish_check_steps.py", entries)
        self.assertIn("agent_finish_final_checks.py", entries)
        self.assertIn(
            f'prefix_rule(pattern=["python3", "{ROOT / "scripts" / "agent-hook.py"}"], decision="allow")',
            entries,
        )
        self.assertNotIn("$HOME", entries)
        self.assertNotIn("${HOME}", entries)
        self.assertNotIn("$AGENTPLAYBOOK_HOME", entries)
        self.assertNotIn("~/", entries)
        self.assertNotIn('", "scripts/', entries)
        self.assertNotIn("--project", entries)
        self.assertNotIn("--request", entries)

    def test_setup_permissions_use_stable_launcher_for_claude(self) -> None:
        entries = "\n".join(claude_permission_entries(ROOT / "scripts", spill_available=False))

        self.assertIn(str(stable_launcher_path()), entries)
        self.assertIn("agentplaybook-hook", entries)
        self.assertNotIn(str(ROOT / "scripts" / "agent-hook.py"), entries)
        self.assertNotIn("python3 scripts/", entries)
        self.assertNotIn("python scripts/", entries)

    def test_setup_permissions_use_absolute_agentplaybook_paths_for_agy(self) -> None:
        entries = "\n".join(agy_permission_entries(ROOT / "scripts", spill_available=False))

        self.assertIn(str(ROOT / "scripts" / "agent-hook.py"), entries)
        self.assertNotIn("$HOME", entries)
        self.assertNotIn("${HOME}", entries)
        self.assertNotIn("$AGENTPLAYBOOK_HOME", entries)
        self.assertNotIn("~/", entries)
        self.assertNotIn("python3 scripts/", entries)
        self.assertNotIn("python scripts/", entries)

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

    def test_runtime_bridge_requires_graph_backed_document_routing(self) -> None:
        agy_block = _agy_runtime_bridge_block(ROOT)
        codex_block = runtime_bridge_block(ROOT, "Codex", "AGENTS.md")
        claude_required = runtime_bridge_required_phrases("Claude", "CLAUDE.md")

        for phrase in RUNTIME_BRIDGE_GRAPH_PHRASES:
            self.assertIn(phrase, AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES)
            self.assertIn(phrase, PREFLIGHT_AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES)
            self.assertIn(phrase, claude_required)
            self.assertIn(phrase, agy_block)
            self.assertIn(phrase, codex_block)

    def test_codex_runtime_bridge_requires_stage_profile_dispatch(self) -> None:
        codex_required = runtime_bridge_required_phrases("Codex", "AGENTS.md")
        codex_block = runtime_bridge_block(ROOT, "Codex", "AGENTS.md")
        claude_block = runtime_bridge_block(ROOT, "Claude", "CLAUDE.md")

        self.assertIn(CODEX_DISPATCH_BRIDGE_PHRASE, codex_required)
        self.assertIn(CODEX_DISPATCH_BRIDGE_PHRASE, codex_block)
        self.assertNotIn(CODEX_DISPATCH_BRIDGE_PHRASE, claude_block)

    def test_setup_hook_runtime_selection_is_scoped(self) -> None:
        from support.setup_agent_hooks_impl import _runtime_selected

        self.assertTrue(_runtime_selected("codex", set()))
        self.assertTrue(_runtime_selected("codex", {"codex"}))
        self.assertFalse(_runtime_selected("claude", {"codex"}))

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
            SOURCE_DOCS_GATE,
            AMBIGUITY_GATE,
            DOCUMENTATION_IMPACT_GATE,
            DOCUMENTATION_GATE,
            TEST_GATE,
            CYCLE_CONTRACT_GATE,
            BOUNDARY_PLAN_GATE,
            MULTI_AGENT_GATE,
            AGENTIC_RUN_STATE_GATE,
            SIDE_EFFECT_AUDIT_GATE,
        ):
            self.assertIn(gate, route["gates"])

        self.assertIn(route_doc("workflows/skills/ambiguity-gate/SKILL.md"), route["docs"])
        self.assertIn(route_doc("workflows/skills/documentation-update/SKILL.md"), route["docs"])
        self.assertIn(route_doc("common/skills/product-spec-to-implementation/SKILL.md"), route["docs"])
        self.assertIn(route_doc("common/skills/source-driven-development/SKILL.md"), route["docs"])
        self.assertIn(route_doc("common/skills/testing/SKILL.md"), route["docs"])
        self.assertIn(route_doc("common/skills/scenario-driven-testing/SKILL.md"), route["docs"])
        self.assertIn(route_doc("common/skills/verification-policy/SKILL.md"), route["docs"])
        self.assertIn(route_doc("common/skills/code-structure-ownership/SKILL.md"), route["docs"])
        self.assertIn(route_doc("workflows/skills/cycle-contract/SKILL.md"), route["docs"])
        self.assertIn(route_doc("workflows/skills/multi-agent-collaboration/SKILL.md"), route["docs"])
        self.assertIn(route_doc("workflows/skills/development-cycle/SKILL.md"), route["docs"])
        self.assertIn(route_doc("common/skills/code-conventions/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/llm-coding-discipline/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/agent-editing-safety/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/testing/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("workflows/skills/ambiguity-gate/SKILL.md"), route["reference_docs"])
        self.assertIn(route_doc("workflows/skills/cycle-contract/SKILL.md"), route["reference_docs"])
        self.assertIn(route_doc("workflows/skills/product-architecture-delivery/SKILL.md"), route["reference_docs"])
        self.assertNotIn(route_doc("workflows/skills/product-architecture-delivery/SKILL.md"), route["required_docs"])
        self.assertLess(
            route["gates"].index(ROUTE_DOCS_READ_GATE),
            route["gates"].index("PRD/ARD applicability"),
        )
        self.assertLess(route["gates"].index(SOURCE_DOCS_GATE), route["gates"].index(AMBIGUITY_GATE))
        self.assertLess(route["gates"].index(SOURCE_DOCS_GATE), route["gates"].index(DOCUMENTATION_IMPACT_GATE))
        self.assertLess(route["gates"].index(DOCUMENTATION_IMPACT_GATE), route["gates"].index("implementation"))
        self.assertLess(route["gates"].index(SOURCE_DOCS_GATE), route["gates"].index("implementation"))
        self.assertLess(route["gates"].index(ROUTE_DOCS_READ_GATE), route["gates"].index(AMBIGUITY_GATE))
        self.assertLess(route["gates"].index(ROUTE_DOCS_READ_GATE), route["gates"].index("implementation"))
        self.assertLess(route["gates"].index(AGENTIC_RUN_STATE_GATE), route["gates"].index("implementation"))
        self.assertLess(route["gates"].index(CYCLE_CONTRACT_GATE), route["gates"].index("implementation"))
        self.assertLess(route["gates"].index(AGENTIC_RUN_STATE_GATE), route["gates"].index(CYCLE_CONTRACT_GATE))

    def test_path_surface_promotes_workflow_docs_to_required_docs(self) -> None:
        route = resolve_docs(
            "task",
            None,
            [],
            request_classified=True,
            surface_paths=["scripts/workflow_route.py"],
        )

        self.assertIn(route_doc("workflows/skills/scripted-agent-workflow/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/ci-cd-automation/SKILL.md"), route["required_docs"])
        self.assertIn("doc_surface_matches", route)
        self.assertTrue(any(match["name"] == "workflow_router" for match in route["doc_surface_matches"]))

    def test_graphify_request_records_selected_project_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            route = resolve_docs(
                "task",
                None,
                [],
                request_classified=True,
                request_text="Set up Graphify for the target project.",
                project_root=project,
            )

        self.assertIn(route_doc("docs/skills/agent-bootstrap/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("docs/skills/graphify-project-integration/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/llm-wiki-documentation/SKILL.md"), route["required_docs"])
        self.assertEqual(False, route["target_project_graphify"]["ready"])
        self.assertIn("graphify readiness", route["gates"])
        self.assertTrue(any(match["name"] == "target_project_graphify" for match in route["doc_surface_matches"]))

    def test_graphify_path_surface_promotes_readiness_docs(self) -> None:
        route = resolve_docs(
            "task",
            None,
            [],
            request_classified=True,
            surface_paths=["scripts/support/setup_agent_hooks_impl.py"],
        )

        self.assertIn(route_doc("docs/skills/agent-bootstrap/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("docs/skills/graphify-project-integration/SKILL.md"), route["required_docs"])
        self.assertIn("graphify readiness", route["gates"])
        self.assertTrue(any(match["name"] == "graphify_integration" for match in route["doc_surface_matches"]))

    def test_classified_graphify_evidence_still_infers_route_concern(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "route",
                "workflow-setup",
                "--project",
                str(ROOT),
                "--request-classified",
                "--classification-evidence",
                "answered direct question; separate actionable clear-scoped Graphify project install and readiness workflow",
                "--format",
                "json",
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        route = json.loads(result.stdout)
        self.assertIn("graphify", route["inferred_concerns"])
        self.assertIn("graphify readiness", route["gates"])
        self.assertIn(
            route_doc("docs/skills/graphify-project-integration/SKILL.md"),
            route["required_docs"],
        )

    def test_graphify_readiness_gate_requires_all_structured_fields(self) -> None:
        evidence, missing = synthesize_gate_evidence(
            "graphify readiness",
            "",
            {
                "cli": "graphify resolved",
                "skill_doc": ".agentplaybook/skills/graphify/SKILL.md read",
                "runtime_links": "Codex Claude and AGY links resolve to canonical skill",
                "git_ownership": "canonical files and runtime symlinks tracked portably",
                "project_integration": "AGENTS section and Codex hook present",
                "graph": (
                    "target graphify-out/graph.json fresh; manifest input coverage complete; "
                    "integrity valid; representative relationship path connected"
                ),
                "query_smoke": "graphify query passed",
            },
            {},
        )

        self.assertEqual([], missing)
        self.assertEqual([], validate_gate_evidence({"graphify readiness": evidence}, ["graphify readiness"]))

        failures = validate_gate_evidence(
            {
                "graphify readiness": (
                    "cli=resolved; skill doc=read; runtime links=canonical; "
                    "git ownership=portable; project integration=installed; "
                    "target graph=present; query smoke=failed"
                )
            },
            ["graphify readiness"],
        )
        self.assertTrue(any("incomplete condition" in failure for failure in failures))

        for graph_state in ("stale", "incomplete", "disconnected"):
            with self.subTest(graph_state=graph_state):
                failures = validate_gate_evidence(
                    {
                        "graphify readiness": (
                            "cli=resolved; skill doc=read; runtime links=canonical; "
                            "git ownership=portable; project integration=installed; "
                            f"target graph={graph_state}; query smoke=succeeded"
                        )
                    },
                    ["graphify readiness"],
                )
                self.assertTrue(
                    any("incomplete condition" in failure for failure in failures)
                )

        for field, value in (
            ("target graph", "dirty"),
            ("target graph", "invalid"),
            ("query smoke", "skipped"),
            ("git ownership", "unknown"),
        ):
            with self.subTest(field=field, value=value):
                values = {
                    "cli": "resolved",
                    "skill doc": "read",
                    "runtime links": "resolve to canonical",
                    "git ownership": "tracked portably",
                    "project integration": "installed",
                    "target graph": (
                        "fresh; manifest input coverage complete; integrity valid; "
                        "relationship path connected"
                    ),
                    "query smoke": "passed",
                }
                values[field] = value
                evidence = "; ".join(f"{key}={item}" for key, item in values.items())
                failures = validate_gate_evidence(
                    {"graphify readiness": evidence}, ["graphify readiness"]
                )
                self.assertTrue(failures)

        _, missing = synthesize_gate_evidence(
            "graphify readiness",
            "",
            {
                "cli": "graphify resolved",
                "skill_doc": "skill read",
                "runtime_links": "links resolve to canonical",
                "git_ownership": "canonical files and symlinks tracked",
                "project_integration": "hook present",
                "graph": "graph present",
            },
            {},
        )
        self.assertEqual(["query_smoke"], missing)

        _, missing = synthesize_gate_evidence(
            "graphify readiness",
            "",
            {
                "cli": "graphify resolved",
                "skill_doc": "skill read",
                "runtime_links": "links resolve to canonical",
                "project_integration": "hook present",
                "graph": "graph present",
                "query_smoke": "query passed",
            },
            {},
        )
        self.assertEqual(["git_ownership"], missing)

    def test_request_path_surface_promotes_docs_without_explicit_keyword(self) -> None:
        route = resolve_docs(
            "task",
            None,
            [],
            request_classified=True,
            request_text="`scripts/workflow_route.py` 수정해줘",
        )

        self.assertIn(route_doc("workflows/skills/scripted-agent-workflow/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/ci-cd-automation/SKILL.md"), route["required_docs"])

    def test_test_path_surface_promotes_testing_docs_to_required_docs(self) -> None:
        route = resolve_docs(
            "task",
            None,
            [],
            request_classified=True,
            surface_paths=["tests/test_workflow_routing.py"],
        )

        self.assertIn(route_doc("common/skills/testing/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/verification-policy/SKILL.md"), route["required_docs"])

    def test_surface_helpers_extract_request_and_git_status_paths(self) -> None:
        self.assertIn(
            "scripts/workflow_request.py",
            extract_request_surface_paths("`scripts/workflow_request.py` 수정해줘"),
        )
        self.assertIn(
            "scripts/workflow_request.py",
            extract_request_surface_paths("`scripts/workflow_request.py:10` 확인해줘"),
        )
        self.assertIn(
            "scripts/workflow_route.py",
            git_status_surface_paths(" M scripts/workflow_route.py\n?? tests/new_test.py\n"),
        )
        self.assertIn(
            "tests/new_test.py",
            git_status_surface_paths(" M scripts/workflow_route.py\n?? tests/new_test.py\n"),
        )

    def test_surface_rule_docs_are_loaded_from_root_map(self) -> None:
        docs, matches = infer_surface_docs(
            command="task",
            surface_paths=["common/skills/code-conventions/SKILL.md"],
        )

        self.assertIn("common/skills/agent-skill-card-anatomy/SKILL.md", docs)
        self.assertIn("docs/skills/agentplaybook-skill-bundle-migration/SKILL.md", docs)
        self.assertTrue(any(match["name"] == "skill_docs" for match in matches))

    def test_skill_bundle_structure_request_promotes_migration_docs(self) -> None:
        route = resolve_docs(
            "docs",
            None,
            [],
            request_classified=True,
            request_text=(
                "skills 폴더와 references 구조를 정리하고 중복 source-of-truth를 줄여줘"
            ),
        )

        self.assertIn(
            route_doc("docs/skills/agentplaybook-skill-bundle-migration/SKILL.md"),
            route["required_docs"],
        )
        self.assertIn(route_doc("common/skills/agent-skill-card-anatomy/SKILL.md"), route["required_docs"])
        self.assertTrue(
            any(match["name"] == "skill_bundle_structure_cleanup" for match in route["doc_surface_matches"])
        )

    def test_surface_doc_sets_are_loaded_from_root_map(self) -> None:
        docs, invalid_refs = surface_rule_doc_refs(load_doc_surface_rules())

        self.assertEqual([], invalid_refs)
        self.assertIn("platforms/web/skills/web-react-ui/SKILL.md", docs)
        self.assertIn("platforms/ios/skills/ios-swiftui-ui/SKILL.md", docs)
        self.assertIn("platforms/flutter/skills/flutter-widget-ui/SKILL.md", docs)

    def test_document_graph_expands_markdown_and_required_frontmatter_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "a.md").write_text(
                "---\nrequires_docs:\n  - docs/c.md\n---\n# A\n\nRead [B](b.md).\n",
                encoding="utf-8",
            )
            (docs_dir / "b.md").write_text("# B\n", encoding="utf-8")
            (docs_dir / "c.md").write_text("# C\n", encoding="utf-8")

            clear_doc_graph_cache()
            matches = expand_doc_matches(root, ["docs/a.md"], max_depth=1)
            paths = [str(match["path"]) for match in matches]

            self.assertIn("docs/b.md", paths)
            self.assertIn("docs/c.md", paths)
            self.assertEqual(["docs/c.md"], graph_required_docs(matches))

    def test_document_graph_expands_surface_rule_neighbors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "a.md").write_text("# A\n", encoding="utf-8")
            (docs_dir / "b.md").write_text("# B\n", encoding="utf-8")
            (root / "workflow-doc-surfaces.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "doc_sets": {"pair": ["docs/a.md", "docs/b.md"]},
                        "request_intents": [],
                        "path_surfaces": [],
                    }
                ),
                encoding="utf-8",
            )

            clear_doc_graph_cache()
            matches = expand_doc_matches(
                root,
                ["docs/a.md"],
                max_depth=1,
                relation_prefixes=("surface:",),
            )

            self.assertIn("docs/b.md", [str(match["path"]) for match in matches])
            self.assertTrue(any(match["relation"] == "surface:doc_set:pair" for match in matches))

    def test_android_ui_request_promotes_compose_docs_to_required_docs(self) -> None:
        route = resolve_docs(
            "feature",
            "android",
            [],
            request_classified=True,
            request_text=(
                "안드로이드 작업에서 첫 화면에서는 전체 목록이, "
                "두번째 화면에서는 즐겨찾기가 있는 화면을 구성해줘"
            ),
        )

        self.assertIn(route_doc("platforms/android/skills/android-compose-ui/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("platforms/android/skills/android-viewmodel-state/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("platforms/android/skills/android-state-data/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/ui-visual-verification/SKILL.md"), route["required_docs"])
        self.assertIn(
            "platforms/android/skills/source-coverage/references/compose-performance-source-map.md",
            route["required_docs"],
        )
        self.assertTrue(any(match["name"] == "android_compose_ui_feature" for match in route["doc_surface_matches"]))

    def test_android_compose_self_selection_promotes_performance_source_docs(self) -> None:
        route = resolve_docs(
            "feature",
            "android",
            [],
            request_classified=True,
            request_text="Compose로 작성하겠다고 정했으면 목록 화면을 구현해줘",
        )

        self.assertIn(route_doc("platforms/android/skills/android-compose-ui/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("platforms/android/skills/android-external-skill-source-coverage/SKILL.md"), route["required_docs"])
        self.assertIn("platforms/android/skills/source-coverage/SKILL.md", route["required_docs"])
        self.assertIn(
            "platforms/android/skills/source-coverage/references/compose-performance-source-map.md",
            route["required_docs"],
        )
        self.assertIn(
            "platforms/android/skills/source-coverage/references/chrisbanes-source-map.md",
            route["required_docs"],
        )

    def test_android_compose_path_promotes_compose_docs_without_request_keyword(self) -> None:
        route = resolve_docs(
            "task",
            None,
            [],
            request_classified=True,
            surface_paths=["app/src/main/java/com/example/home/HomeScreen.kt"],
        )

        self.assertIn(route_doc("platforms/android/skills/android-compose-ui/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("platforms/android/skills/android-review/SKILL.md"), route["required_docs"])
        self.assertIn(
            "platforms/android/skills/source-coverage/references/compose-performance-source-map.md",
            route["required_docs"],
        )
        self.assertTrue(any(match["name"] == "android_compose_paths" for match in route["doc_surface_matches"]))

    def test_query_expands_code_cleanup_natural_language_to_refactor_docs(self) -> None:
        results = search_docs(ROOT, "코드 정리해줘", max_results=8)
        paths = [str(item["path"]) for item in results]

        self.assertIn("workflows/skills/refactor-cleanup/SKILL.md", paths)
        self.assertIn("common/skills/refactoring/SKILL.md", paths)
        self.assertIn("common/skills/verification-policy/SKILL.md", paths)
        self.assertTrue(
            any("code_cleanup" in item.get("matched_facets", []) for item in results),
            results,
        )

    def test_query_uses_wikimap_section_results_behind_existing_api(self) -> None:
        outcome = search_docs_outcome(
            ROOT,
            "When may documentation be skipped with user approval?",
            max_results=8,
        )

        self.assertEqual("wikimap", outcome.backend)
        self.assertEqual("1.0.0", outcome.backend_version)
        self.assertTrue(outcome.results)
        self.assertTrue(
            any(item.get("line") and item.get("heading") for item in outcome.results),
            outcome.results,
        )

    def test_query_expands_android_ui_natural_language_to_compose_docs(self) -> None:
        results = search_docs(
            ROOT,
            "안드로이드 첫 화면에서는 전체 목록이, 두번째 화면에서는 즐겨찾기가 있는 화면을 구성해줘",
            max_results=16,
        )
        paths = [str(item["path"]) for item in results]

        self.assertIn("platforms/android/skills/android-compose-ui/SKILL.md", paths)
        self.assertIn("platforms/android/skills/android-viewmodel-state/SKILL.md", paths)
        self.assertIn("platforms/android/skills/source-coverage/references/compose-performance-source-map.md", paths)
        self.assertTrue(
            any("android_compose_ui" in item.get("matched_facets", []) for item in results),
            results,
        )

    def test_natural_language_doc_routing_request_promotes_workflow_docs(self) -> None:
        route = resolve_docs(
            "workflow-setup",
            None,
            [],
            request_classified=True,
            request_text="훅은 보완이고 자연어 검색 가능한 문서 라우팅을 강화해줘",
        )

        self.assertIn(route_doc("workflows/skills/scripted-agent-workflow/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/task-intake-effort-routing/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/source-driven-development/SKILL.md"), route["required_docs"])
        self.assertTrue(any(match["name"] == "natural_language_doc_routing" for match in route["doc_surface_matches"]))
        self.assertEqual("wikimap", route["document_search"]["backend"])
        self.assertTrue(route["document_search"]["candidates"])
        self.assertTrue(
            set(route["document_search"]["candidates"]).issubset(
                set(route["required_docs"]) | set(route["reference_docs"])
            )
        )

    def test_planning_change_request_promotes_documentation_impact_docs(self) -> None:
        route = resolve_docs(
            "task",
            None,
            [],
            request_classified=True,
            request_text="기획변경인데 예상 문서 정리가 누락되는 경우를 막아줘",
        )

        self.assertIn(route_doc("common/skills/doc-conventions/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("workflows/skills/documentation-update/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/product-spec-to-implementation/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/source-driven-development/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("common/skills/definition-of-done/SKILL.md"), route["required_docs"])
        self.assertIn(route_doc("workflows/skills/scripted-agent-workflow/SKILL.md"), route["required_docs"])
        self.assertTrue(any(match["name"] == "planning_change_documentation" for match in route["doc_surface_matches"]))

    def test_route_exposes_document_graph_neighbors_as_reference_docs(self) -> None:
        route = resolve_docs(
            "workflow-setup",
            None,
            [],
            request_classified=True,
            request_text="훅은 보완이고 자연어 검색 가능한 문서 라우팅을 강화해줘",
        )

        self.assertIn("doc_graph_matches", route)
        self.assertIn(
            "workflows/skills/scripted-agent-workflow/references/current-guidance.md",
            route["reference_docs"],
        )
        self.assertNotIn(
            "workflows/skills/scripted-agent-workflow/references/current-guidance.md",
            route["required_docs"],
        )

    def test_query_uses_document_graph_to_promote_related_skill_entrypoints(self) -> None:
        results = search_docs(ROOT, "훅으로 문서 검색하고 읽도록", max_results=12)
        graph_items = [
            item
            for item in results
            if item["path"] == "workflows/skills/scripted-agent-workflow/SKILL.md"
        ]

        self.assertTrue(graph_items, results)
        self.assertTrue(
            graph_items[0].get("graph_reasons")
            or "natural_language_doc_routing" in graph_items[0].get("matched_facets", []),
            graph_items[0],
        )

    def test_query_promotes_skill_bundle_migration_for_structure_cleanup(self) -> None:
        results = search_docs(
            ROOT,
            "스킬 references 구조와 중복 source-of-truth 정리",
            max_results=12,
        )

        self.assertTrue(
            any(
                item["path"] == "docs/skills/agentplaybook-skill-bundle-migration/SKILL.md"
                for item in results
            ),
            results,
        )

    def test_ui_feature_request_promotes_docs_for_all_ui_platforms(self) -> None:
        request = "첫 화면에서는 전체 목록이, 두번째 화면에서는 즐겨찾기가 있는 화면을 구성해줘"
        expected_docs = {
            "android": [
                "platforms/android/skills/android-compose-ui/SKILL.md",
                "platforms/android/skills/android-viewmodel-state/SKILL.md",
                "platforms/android/skills/source-coverage/references/compose-performance-source-map.md",
            ],
            "application": [
                "platforms/application/skills/application-command-ui/SKILL.md",
                "platforms/application/skills/application-system-integration/SKILL.md",
            ],
            "flutter": [
                "platforms/flutter/skills/flutter-widget-ui/SKILL.md",
                "platforms/flutter/skills/flutter-state-data/SKILL.md",
            ],
            "ios": [
                "platforms/ios/skills/ios-swiftui-ui/SKILL.md",
                "platforms/ios/skills/ios-uikit-ui/SKILL.md",
                "platforms/ios/skills/ios-state-concurrency/SKILL.md",
            ],
            "kmp": [
                "platforms/kmp/skills/kmp-compose-ui/SKILL.md",
                "platforms/kmp/skills/kmp-state-data/SKILL.md",
            ],
            "swift": [
                "platforms/swift/skills/swift-design-system/SKILL.md",
                "platforms/swift/skills/swift-code-structure/SKILL.md",
            ],
            "web": [
                "platforms/web/skills/web-react-ui/SKILL.md",
                "platforms/web/skills/web-state-data/SKILL.md",
                "platforms/web/skills/web-design-system/SKILL.md",
            ],
        }

        for platform, docs in expected_docs.items():
            with self.subTest(platform=platform):
                route = resolve_docs(
                    "feature",
                    platform,
                    [],
                    request_classified=True,
                    request_text=request,
                )

                for doc in docs:
                    self.assertIn(route_doc(doc), route["required_docs"])
                self.assertIn(route_doc("common/skills/ui-visual-verification/SKILL.md"), route["required_docs"])
                self.assertIn(route_doc("common/skills/performance-verification/SKILL.md"), route["required_docs"])

    def test_server_platform_does_not_receive_ui_surface_docs(self) -> None:
        route = resolve_docs(
            "feature",
            "server",
            [],
            request_classified=True,
            request_text="첫 화면에서는 전체 목록이, 두번째 화면에서는 즐겨찾기가 있는 화면을 구성해줘",
        )

        self.assertNotIn("doc_surface_matches", route)
        self.assertNotIn(route_doc("common/skills/ui-visual-verification/SKILL.md"), route["required_docs"])
        self.assertNotIn(route_doc("platforms/web/skills/web-react-ui/SKILL.md"), route["required_docs"])

    def test_self_selected_ui_frameworks_promote_platform_docs(self) -> None:
        cases = [
            (
                "android",
                "Compose로 목록 화면을 구현해줘",
                "android_compose_self_selected",
                "platforms/android/skills/android-compose-ui/SKILL.md",
            ),
            (
                "application",
                "Tauri React renderer로 목록 화면을 구현해줘",
                "application_react_self_selected",
                "platforms/application/skills/application-react-desktop/SKILL.md",
            ),
            (
                "flutter",
                "Flutter Widget으로 목록 화면을 구현해줘",
                "flutter_widget_self_selected",
                "platforms/flutter/skills/flutter-widget-ui/SKILL.md",
            ),
            (
                "ios",
                "SwiftUI로 목록 화면을 구현해줘",
                "ios_swiftui_self_selected",
                "platforms/ios/skills/ios-swiftui-ui/SKILL.md",
            ),
            (
                "ios",
                "UIKit ViewController로 목록 화면을 구현해줘",
                "ios_uikit_self_selected",
                "platforms/ios/skills/ios-uikit-ui/SKILL.md",
            ),
            (
                "kmp",
                "Compose Multiplatform으로 목록 화면을 구현해줘",
                "kmp_compose_self_selected",
                "platforms/kmp/skills/kmp-compose-ui/SKILL.md",
            ),
            (
                "web",
                "React TSX로 목록 화면을 구현해줘",
                "web_react_self_selected",
                "platforms/web/skills/web-react-ui/SKILL.md",
            ),
        ]

        for platform, request, match_name, doc in cases:
            with self.subTest(platform=platform, match_name=match_name):
                route = resolve_docs(
                    "feature",
                    platform,
                    [],
                    request_classified=True,
                    request_text=request,
                )

                self.assertIn(route_doc(doc), route["required_docs"])
                self.assertTrue(any(match["name"] == match_name for match in route["doc_surface_matches"]))

    def test_ui_path_surfaces_promote_platform_docs_without_cross_platform_leak(self) -> None:
        cases = [
            (
                "app/src/main/java/com/example/home/HomeScreen.kt",
                "android_compose_paths",
                "platforms/android/skills/android-compose-ui/SKILL.md",
                "platforms/kmp/skills/kmp-compose-ui/SKILL.md",
            ),
            (
                "shared/src/commonMain/kotlin/com/example/home/HomeScreen.kt",
                "kmp_compose_paths",
                "platforms/kmp/skills/kmp-compose-ui/SKILL.md",
                "platforms/android/skills/android-compose-ui/SKILL.md",
            ),
            (
                "src/features/home/HomeScreen.tsx",
                "web_react_paths",
                "platforms/web/skills/web-react-ui/SKILL.md",
                "platforms/application/skills/application-command-ui/SKILL.md",
            ),
            (
                "App/Features/Home/HomeView.swift",
                "ios_swiftui_paths",
                "platforms/ios/skills/ios-swiftui-ui/SKILL.md",
                "platforms/ios/skills/ios-uikit-ui/SKILL.md",
            ),
            (
                "App/Features/Home/HomeViewController.swift",
                "ios_uikit_paths",
                "platforms/ios/skills/ios-uikit-ui/SKILL.md",
                "platforms/kmp/skills/kmp-compose-ui/SKILL.md",
            ),
            (
                "lib/features/home/screens/home_screen.dart",
                "flutter_widget_paths",
                "platforms/flutter/skills/flutter-widget-ui/SKILL.md",
                "platforms/web/skills/web-react-ui/SKILL.md",
            ),
            (
                "Sources/AppDesignSystem/Components/ButtonStyle.swift",
                "swift_design_paths",
                "platforms/swift/skills/swift-design-system/SKILL.md",
                "platforms/ios/skills/ios-uikit-ui/SKILL.md",
            ),
            (
                "src-tauri/src/main.rs",
                "application_desktop_paths",
                "platforms/application/skills/application-command-ui/SKILL.md",
                "platforms/web/skills/web-react-ui/SKILL.md",
            ),
        ]

        for path, match_name, expected_doc, absent_doc in cases:
            with self.subTest(path=path):
                route = resolve_docs(
                    "task",
                    None,
                    [],
                    request_classified=True,
                    surface_paths=[path],
                )

                self.assertIn(route_doc(expected_doc), route["required_docs"])
                self.assertNotIn(route_doc(absent_doc), route["required_docs"])
                self.assertTrue(any(match["name"] == match_name for match in route["doc_surface_matches"]))

    def test_routes_expose_parallel_execution_plan(self) -> None:
        route = resolve_docs("feature", None, ["testing"], request_classified=True)
        plan = route["parallel_execution"]
        phases = {phase["id"]: phase for phase in plan["phases"]}

        self.assertEqual(1, plan["schema_version"])
        self.assertEqual([], validate_parallel_execution_plan(plan, route["gates"]))
        self.assertEqual("parallel", phases["orientation"]["mode"])
        self.assertIn(ROUTE_DOCS_READ_GATE, phases["orientation"]["gates"])
        self.assertEqual("conditional_parallel", phases["implementation"]["mode"])
        self.assertIn(MULTI_AGENT_GATE, phases["implementation"]["gates"])
        self.assertEqual("serial", phases["integration_review"]["mode"])
        self.assertIn("review hook", phases["integration_review"]["gates"])
        self.assertEqual("parallel", phases["verification"]["mode"])
        self.assertIn(TEST_GATE, phases["verification"]["gates"])

    def test_multi_agent_route_exposes_worker_parallel_phase(self) -> None:
        route = resolve_docs("multi-agent", None, [], request_classified=True)
        phases = {phase["id"]: phase for phase in route["parallel_execution"]["phases"]}

        self.assertEqual([], validate_parallel_execution_plan(route["parallel_execution"], route["gates"]))
        self.assertEqual("serial", phases["scoping"]["mode"])
        self.assertIn(AGENTIC_RUN_STATE_GATE, phases["scoping"]["gates"])
        self.assertEqual("parallel", phases["worker_execution"]["mode"])
        self.assertIn("roles", phases["worker_execution"]["gates"])
        self.assertIn("write scopes", phases["worker_execution"]["gates"])
        self.assertEqual("serial", phases["integration_review"]["mode"])
        self.assertIn("integration review", phases["integration_review"]["gates"])

    def test_work_producing_routes_get_cycle_contract_but_review_stays_separate(self) -> None:
        for command in sorted(WORK_PRODUCING_COMMANDS):
            with self.subTest(command=command):
                route = resolve_docs(command, None, [], request_classified=True)

                self.assertIn(CYCLE_CONTRACT_GATE, route["gates"])
                self.assertIn(route_doc("workflows/skills/cycle-contract/SKILL.md"), route["docs"])

        for command in ("review", "docs-review", "test", "multi-agent", "triage"):
            with self.subTest(command=command):
                route = resolve_docs(command, None, [], request_classified=True)

                self.assertNotIn(CYCLE_CONTRACT_GATE, route["gates"])

    def test_source_docs_gate_covers_policy_and_repair_workflows(self) -> None:
        implementation_anchors = {
            "bugfix": "fix",
            "code-simplify": "small refactor",
            "refactor": "small refactor",
            "workflow-setup": "install or repair",
        }
        for command in ("bugfix", "code-simplify", "refactor", "workflow-setup"):
            with self.subTest(command=command):
                route = resolve_docs(command, None, [], request_classified=True)

                self.assertIn(SOURCE_DOCS_GATE, route["gates"])
                self.assertIn(DOCUMENTATION_IMPACT_GATE, route["gates"])
                self.assertIn(CYCLE_CONTRACT_GATE, route["gates"])
                self.assertIn(route_doc("common/skills/source-driven-development/SKILL.md"), route["docs"])
                self.assertIn(route_doc("workflows/skills/cycle-contract/SKILL.md"), route["docs"])
                implementation_anchor = implementation_anchors[command]
                self.assertLess(
                    route["gates"].index(DOCUMENTATION_IMPACT_GATE),
                    route["gates"].index(implementation_anchor),
                )
                self.assertLess(route["gates"].index(CYCLE_CONTRACT_GATE), route["gates"].index(implementation_anchor))
                self.assertLess(route["gates"].index(SOURCE_DOCS_GATE), route["gates"].index(AMBIGUITY_GATE))

    def test_multi_agent_route_requires_agentic_run_state(self) -> None:
        route = resolve_docs("multi-agent", None, [], request_classified=True)

        self.assertIn(AGENTIC_RUN_STATE_GATE, route["gates"])
        self.assertIn(route_doc("workflows/skills/scripted-agent-workflow/SKILL.md"), route["docs"])
        self.assertLess(route["gates"].index(AGENTIC_RUN_STATE_GATE), route["gates"].index("roles"))
        for gate in ("roles", "write scopes", "agent briefs", "integration review"):
            self.assertIn(gate, VALIDATED_GATES)

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

    def test_finish_evidence_examples_for_doc_impact_and_multi_agent_pass(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_IMPACT_GATE: (
                    "pre-code/pre-edit artifact selection: workflow card and README; "
                    "impact decision: not applicable; reason: no durable behavior, "
                    "no workflow policy, no public contract, no operator action, "
                    "and no acceptance criteria changed, so this does not require "
                    "creating/updating that artifact"
                ),
                MULTI_AGENT_GATE: (
                    "serial/single-agent decision; concrete reason: small "
                    "same-file/same-boundary scope with overlapping contract risk, "
                    "so parallel subagents were not safe; verification: workflow "
                    "validate plus focused unit tests"
                ),
            },
            [DOCUMENTATION_IMPACT_GATE, MULTI_AGENT_GATE],
        )

        self.assertEqual([], failures)

    def test_cycle_contract_evidence_requires_bounded_cycle_details(self) -> None:
        failures = validate_gate_evidence(
            {CYCLE_CONTRACT_GATE: "cycle contract completed"},
            [CYCLE_CONTRACT_GATE],
        )

        self.assertTrue(any("cycle contract evidence" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                CYCLE_CONTRACT_GATE: (
                    "cycle_type=workflow_setup; input_scope=router workflow policy; "
                    "allowed_changes=workflow docs, route gates, finish-check validators, tests; "
                    "forbidden_changes=unrelated dirty files, external runtime config, deploys; "
                    "acceptance criteria=routes include a bounded cycle gate; "
                    "verification=unit tests and workflow validate; "
                    "stop condition=cycle gate is routed, documented, and validated; "
                    "checkpoint=handoff for separate review cycle"
                )
            },
            [CYCLE_CONTRACT_GATE],
        )

        self.assertEqual([], failures)

    def test_gate_evidence_ledger_synthesizes_structured_finish_evidence(self) -> None:
        route = {
            "command": "workflow-setup",
            "docs": ["AGENTS.md"],
            "gates": [ROUTE_DOCS_READ_GATE, CYCLE_CONTRACT_GATE],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "preflight.json"
            preflight = {"route": route}
            evidence_path.write_text(json.dumps(preflight), encoding="utf-8")
            reset_gate_evidence_ledger(evidence_path, preflight)

            record_gate_evidence(
                evidence_path=evidence_path,
                preflight=preflight,
                gate=ROUTE_DOCS_READ_GATE,
                fields={
                    "takeaway": "use structured ledger evidence instead of manual finish prose",
                    "next_action": "record route-doc gate evidence before continuing implementation",
                },
                source="docs-read",
            )
            record_gate_evidence(
                evidence_path=evidence_path,
                preflight=preflight,
                gate=CYCLE_CONTRACT_GATE,
                fields={
                    "cycle_type": "workflow_setup",
                    "input_scope": "finish evidence workflow policy",
                    "allowed_changes": "hook ledger, finish-check merge, tests, docs",
                    "forbidden_changes": "unrelated dirty worktree and external state",
                    "acceptance_criteria": "finish can read current structured gate ledger",
                    "verification": "unit tests and workflow validate",
                    "stop_condition": "ledger evidence is merged and validated",
                    "checkpoint": "handoff",
                },
                source="manual",
            )
            receipt = {
                "schema_version": 1,
                "route_fingerprint": route_fingerprint(route),
                "doc_count": 1,
                "preflight_evidence": str(evidence_path),
                "preflight_evidence_sha256": preflight_evidence_sha256(evidence_path),
                "docs": [{"path": "AGENTS.md", "size_bytes": 1, "sha256": "abc"}],
            }

            gate_evidence, diagnostics = merge_gate_evidence_from_ledger(
                route=route,
                evidence_path=evidence_path,
                route_docs_receipt=receipt,
                cli_gate_evidence={},
            )
            route_docs_failures = validate_route_docs_manifest_evidence(
                route,
                gate_evidence,
                receipt,
                evidence_path,
            )

            self.assertTrue(gate_evidence_path_for_preflight(evidence_path).exists())
            self.assertTrue(diagnostics["used"])
            self.assertIn(ROUTE_DOCS_READ_GATE, gate_evidence)
            self.assertIn(CYCLE_CONTRACT_GATE, gate_evidence)
            self.assertEqual([], validate_gate_evidence(gate_evidence, route["gates"]))
            self.assertEqual([], route_docs_failures)

    def test_gate_evidence_ledger_requires_structured_fields_for_structured_gates(self) -> None:
        route = {
            "command": "workflow-setup",
            "docs": ["AGENTS.md"],
            "gates": [CYCLE_CONTRACT_GATE],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "preflight.json"
            preflight = {"route": route}
            evidence_path.write_text(json.dumps(preflight), encoding="utf-8")
            reset_gate_evidence_ledger(evidence_path, preflight)

            record_gate_evidence(
                evidence_path=evidence_path,
                preflight=preflight,
                gate=CYCLE_CONTRACT_GATE,
                evidence=(
                    "cycle_type=workflow_setup; input_scope=gate evidence ledger fallback; "
                    "allowed_changes=finish-check merge code and tests; "
                    "forbidden_changes=unrelated workflow behavior; "
                    "acceptance criteria=manual ledger evidence is still validated by finish; "
                    "verification=unit test; stop condition=manual evidence merges; "
                    "checkpoint=finish hook retry"
                ),
                source="manual",
            )

            gate_evidence, diagnostics = merge_gate_evidence_from_ledger(
                route=route,
                evidence_path=evidence_path,
                route_docs_receipt={},
                cli_gate_evidence={},
            )

        self.assertFalse(diagnostics["used"])
        self.assertIn(CYCLE_CONTRACT_GATE, diagnostics["missing_fields"])
        self.assertNotIn(CYCLE_CONTRACT_GATE, gate_evidence)

    def test_gate_evidence_ledger_rejects_same_route_preflight_hash_refresh(self) -> None:
        route = {
            "command": "workflow-setup",
            "docs": ["AGENTS.md"],
            "gates": [TEST_GATE, CYCLE_CONTRACT_GATE],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "preflight.json"
            preflight = {"route": route, "git_status": {"stdout": "before"}}
            evidence_path.write_text(json.dumps(preflight), encoding="utf-8")
            reset_gate_evidence_ledger(evidence_path, preflight)
            record_gate_evidence(
                evidence_path=evidence_path,
                preflight=preflight,
                gate=TEST_GATE,
                evidence="test/check run: first check; result: PASS",
                source="manual",
            )

            refreshed_preflight = {"route": route, "git_status": {"stdout": "after"}}
            evidence_path.write_text(json.dumps(refreshed_preflight), encoding="utf-8")
            record_gate_evidence(
                evidence_path=evidence_path,
                preflight=refreshed_preflight,
                gate=CYCLE_CONTRACT_GATE,
                fields={
                    "cycle_type": "workflow_setup",
                    "input_scope": "same route ledger refresh",
                    "allowed_changes": "gate evidence binding",
                    "forbidden_changes": "route changes",
                    "acceptance_criteria": "existing gate evidence remains after hash refresh",
                    "verification": "unit test",
                    "stop_condition": "ledger keeps both entries",
                    "checkpoint": "finish hook",
                },
                source="manual",
            )

            gate_evidence, diagnostics = merge_gate_evidence_from_ledger(
                route=route,
                evidence_path=evidence_path,
                route_docs_receipt={},
                cli_gate_evidence={},
            )

        self.assertTrue(diagnostics["used"])
        self.assertNotIn(TEST_GATE, gate_evidence)
        self.assertIn(CYCLE_CONTRACT_GATE, gate_evidence)
        self.assertEqual([], validate_gate_evidence(gate_evidence, route["gates"]))

    def test_gate_evidence_ledger_rejects_partial_structured_fields_even_with_text(self) -> None:
        route = {
            "command": "workflow-setup",
            "docs": ["AGENTS.md"],
            "gates": [CYCLE_CONTRACT_GATE],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "preflight.json"
            preflight = {"route": route}
            evidence_path.write_text(json.dumps(preflight), encoding="utf-8")
            reset_gate_evidence_ledger(evidence_path, preflight)

            record_gate_evidence(
                evidence_path=evidence_path,
                preflight=preflight,
                gate=CYCLE_CONTRACT_GATE,
                evidence=(
                    "cycle_type=workflow_setup; input_scope=partial fields; "
                    "allowed_changes=tests; forbidden_changes=none; "
                    "acceptance criteria=must not bypass fields; verification=unit test; "
                    "stop condition=done; checkpoint=finish"
                ),
                fields={
                    "cycle_type": "workflow_setup",
                    "input_scope": "partial fields",
                },
                source="manual",
            )

            gate_evidence, diagnostics = merge_gate_evidence_from_ledger(
                route=route,
                evidence_path=evidence_path,
                route_docs_receipt={},
                cli_gate_evidence={},
            )

        self.assertNotIn(CYCLE_CONTRACT_GATE, gate_evidence)
        self.assertIn(CYCLE_CONTRACT_GATE, diagnostics["missing_fields"])

    def test_record_many_gate_evidence_writes_batch_with_single_binding(self) -> None:
        route = {
            "command": "workflow-setup",
            "docs": ["AGENTS.md"],
            "gates": [BOUNDARY_PLAN_GATE, TEST_GATE],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "preflight.json"
            preflight = {"route": route}
            evidence_path.write_text(json.dumps(preflight), encoding="utf-8")

            entries = record_many_gate_evidence(
                evidence_path=evidence_path,
                preflight=preflight,
                records=[
                    {
                        "gate": BOUNDARY_PLAN_GATE,
                        "fields": {
                            "scope": "gate evidence batching",
                            "verification": "unit test",
                        },
                    },
                    {
                        "gate": TEST_GATE,
                        "fields": {
                            "check": "unit test",
                            "result": "PASS",
                        },
                    },
                ],
            )

            ledger_path = gate_evidence_path_for_preflight(evidence_path)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            gate_evidence, diagnostics = merge_gate_evidence_from_ledger(
                route=route,
                evidence_path=evidence_path,
                route_docs_receipt={},
                cli_gate_evidence={},
            )

        self.assertEqual(2, len(entries))
        self.assertEqual(2, len(ledger["entries"]))
        self.assertTrue(diagnostics["used"])
        self.assertIn(BOUNDARY_PLAN_GATE, gate_evidence)
        self.assertIn(TEST_GATE, gate_evidence)
        self.assertEqual([], validate_gate_evidence(gate_evidence, route["gates"]))

    def test_custom_preflight_evidence_uses_separate_gate_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            default_evidence = root / ".agentplaybook" / "preflight.json"
            custom_evidence = root / ".agentplaybook" / "preflight-smoke.json"
            default_evidence.parent.mkdir(parents=True)

            self.assertEqual(
                default_evidence.parent / "gate-evidence.json",
                gate_evidence_path_for_preflight(default_evidence),
            )
            self.assertEqual(
                custom_evidence.parent / "preflight-smoke-gate-evidence.json",
                gate_evidence_path_for_preflight(custom_evidence),
            )

    def test_agent_hook_gate_batch_cli_records_multiple_gates(self) -> None:
        route = {
            "command": "workflow-setup",
            "docs": ["AGENTS.md"],
            "gates": [BOUNDARY_PLAN_GATE, TEST_GATE],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            evidence_path = project / ".agentplaybook" / "preflight.json"
            evidence_path.parent.mkdir(parents=True)
            evidence_path.write_text(json.dumps({"route": route}), encoding="utf-8")
            records = [
                {
                    "gate": BOUNDARY_PLAN_GATE,
                    "fields": {
                        "scope": "gate evidence batch cli",
                        "verification": "subprocess test",
                    },
                },
                {
                    "gate": TEST_GATE,
                    "fields": {
                        "check": "subprocess test",
                        "result": "PASS",
                    },
                },
            ]

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "agent-hook.py"),
                    "gate-batch",
                    "--project",
                    str(project),
                    "--rules",
                    str(ROOT),
                    "--evidence",
                    str(evidence_path),
                    "--gate-record",
                    json.dumps(records),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            ledger_path = gate_evidence_path_for_preflight(evidence_path)
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("SUCCESS gate-batch", result.stdout)
        self.assertIn("2 gate evidence entries recorded", result.stdout)
        self.assertEqual([BOUNDARY_PLAN_GATE, TEST_GATE], [entry["gate"] for entry in ledger["entries"]])

    def test_vibeguard_cache_reuses_same_git_state_and_invalidates_on_status_change(self) -> None:
        calls: list[list[str]] = []
        state = {"status": ""}

        def run_command(command: list[str], cwd: Path) -> dict[str, object]:
            calls.append(command)
            if command[:3] == ["git", "rev-parse", "--verify"]:
                return {
                    "command": command,
                    "cwd": str(cwd),
                    "returncode": 0,
                    "stdout": "abc123\n",
                    "stderr": "",
                }
            if command[:3] == ["git", "status", "--short"]:
                return {
                    "command": command,
                    "cwd": str(cwd),
                    "returncode": 0,
                    "stdout": state["status"],
                    "stderr": "",
                }
            if command == ["vibeguard", "audit", "."]:
                return {
                    "command": command,
                    "cwd": str(cwd),
                    "returncode": 0,
                    "stdout": "Overall: Ready\n",
                    "stderr": "",
                }
            raise AssertionError(command)

        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            rules = project
            command = lambda _project, _rules: ["vibeguard", "audit", "."]
            parse = lambda output: "Ready" if "Ready" in output else "unknown"

            first = cached_vibeguard(
                project=project,
                rules=rules,
                run_command=run_command,
                vibeguard_command=command,
                parse_overall=parse,
            )
            second = cached_vibeguard(
                project=project,
                rules=rules,
                run_command=run_command,
                vibeguard_command=command,
                parse_overall=parse,
            )
            state["status"] = " M scripts/agent-hook.py\n"
            third = cached_vibeguard(
                project=project,
                rules=rules,
                run_command=run_command,
                vibeguard_command=command,
                parse_overall=parse,
            )

        audit_calls = [command for command in calls if command == ["vibeguard", "audit", "."]]
        self.assertEqual(2, len(audit_calls))
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertFalse(third["cached"])

    def test_vibeguard_cache_invalidates_on_rules_git_state_change(self) -> None:
        calls: list[tuple[Path, list[str]]] = []
        states = {"project": "", "rules": ""}

        def run_command(command: list[str], cwd: Path) -> dict[str, object]:
            calls.append((cwd, command))
            if command[:3] == ["git", "rev-parse", "--verify"]:
                return {
                    "command": command,
                    "cwd": str(cwd),
                    "returncode": 0,
                    "stdout": f"{cwd.name}-head\n",
                    "stderr": "",
                }
            if command[:3] == ["git", "status", "--short"]:
                return {
                    "command": command,
                    "cwd": str(cwd),
                    "returncode": 0,
                    "stdout": states[cwd.name],
                    "stderr": "",
                }
            if command == ["vibeguard", "audit", "."]:
                return {
                    "command": command,
                    "cwd": str(cwd),
                    "returncode": 0,
                    "stdout": "Overall: Ready\n",
                    "stderr": "",
                }
            raise AssertionError(command)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            rules = root / "rules"
            project.mkdir()
            rules.mkdir()
            command = lambda _project, _rules: ["vibeguard", "audit", "."]
            parse = lambda output: "Ready" if "Ready" in output else "unknown"

            first = cached_vibeguard(
                project=project,
                rules=rules,
                run_command=run_command,
                vibeguard_command=command,
                parse_overall=parse,
            )
            second = cached_vibeguard(
                project=project,
                rules=rules,
                run_command=run_command,
                vibeguard_command=command,
                parse_overall=parse,
            )
            states["rules"] = " M common/rules.md\n"
            third = cached_vibeguard(
                project=project,
                rules=rules,
                run_command=run_command,
                vibeguard_command=command,
                parse_overall=parse,
            )

        audit_calls = [command for _cwd, command in calls if command == ["vibeguard", "audit", "."]]
        self.assertEqual(2, len(audit_calls))
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertFalse(third["cached"])

    def test_vibeguard_cache_does_not_store_failed_invocations(self) -> None:
        calls: list[list[str]] = []

        def run_command(command: list[str], cwd: Path) -> dict[str, object]:
            calls.append(command)
            if command[:3] == ["git", "rev-parse", "--verify"]:
                return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "abc\n", "stderr": ""}
            if command[:3] == ["git", "status", "--short"]:
                return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "", "stderr": ""}
            if command == ["vibeguard", "audit", "."]:
                return {
                    "command": command,
                    "cwd": str(cwd),
                    "returncode": 1,
                    "stdout": "",
                    "stderr": "temporary failure",
                }
            raise AssertionError(command)

        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            command = lambda _project, _rules: ["vibeguard", "audit", "."]
            parse = lambda output: "Ready" if "Ready" in output else "unknown"

            first = cached_vibeguard(
                project=project,
                rules=project,
                run_command=run_command,
                vibeguard_command=command,
                parse_overall=parse,
            )
            second = cached_vibeguard(
                project=project,
                rules=project,
                run_command=run_command,
                vibeguard_command=command,
                parse_overall=parse,
            )

        audit_calls = [command for command in calls if command == ["vibeguard", "audit", "."]]
        self.assertEqual(2, len(audit_calls))
        self.assertFalse(first["cached"])
        self.assertFalse(second["cached"])

    def test_vibeguard_cache_ignores_preexisting_failed_cache_entry(self) -> None:
        calls: list[list[str]] = []

        def run_command(command: list[str], cwd: Path) -> dict[str, object]:
            calls.append(command)
            if command[:3] == ["git", "rev-parse", "--verify"]:
                return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "abc\n", "stderr": ""}
            if command[:3] == ["git", "status", "--short"]:
                return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "", "stderr": ""}
            if command == ["vibeguard", "audit", "."]:
                return {
                    "command": command,
                    "cwd": str(cwd),
                    "returncode": 0,
                    "stdout": "Overall: Ready\n",
                    "stderr": "",
                }
            raise AssertionError(command)

        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            command = lambda _project, _rules: ["vibeguard", "audit", "."]
            parse = lambda output: "Ready" if "Ready" in output else "unknown"

            first = cached_vibeguard(
                project=project,
                rules=project,
                run_command=run_command,
                vibeguard_command=command,
                parse_overall=parse,
            )
            cache_path = project / ".agentplaybook" / "vibeguard-cache.json"
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            payload["result"]["returncode"] = 1
            payload["result"]["stderr"] = "old failure"
            cache_path.write_text(json.dumps(payload), encoding="utf-8")

            second = cached_vibeguard(
                project=project,
                rules=project,
                run_command=run_command,
                vibeguard_command=command,
                parse_overall=parse,
            )

        audit_calls = [command for command in calls if command == ["vibeguard", "audit", "."]]
        self.assertEqual(2, len(audit_calls))
        self.assertFalse(first["cached"])
        self.assertFalse(second["cached"])

    def test_review_hook_detects_mutation_outside_pathspec(self) -> None:
        full_statuses = [
            " M outside.py\n",
            " M outside.py\n M outside2.py\n",
        ]
        outputs: list[dict[str, object]] = []

        def git_status(_project: Path) -> tuple[dict[str, object], list[str]]:
            stdout = full_statuses.pop(0)
            result = {
                "command": ["git", "status", "--short", "--untracked-files=all"],
                "cwd": str(ROOT),
                "returncode": 0,
                "stdout": stdout,
                "stderr": "",
            }
            return result, [line for line in stdout.splitlines() if line.strip()]

        def run_command(command: list[str], cwd: Path) -> dict[str, object]:
            if command[:3] == ["git", "status", "--short"]:
                return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "", "stderr": ""}
            if command[:3] == ["git", "rev-parse", "--verify"]:
                return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "abc\n", "stderr": ""}
            if command[:2] == ["git", "diff"]:
                return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "", "stderr": ""}
            if command[:2] == ["git", "ls-files"]:
                return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "", "stderr": ""}
            if command == ["vibeguard", "--help"]:
                return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "", "stderr": ""}
            if command[:3] == ["vibeguard", "audit", "."]:
                return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "Overall: Ready\n", "stderr": ""}
            return {"command": command, "cwd": str(cwd), "returncode": 0, "stdout": "", "stderr": ""}

        def finish_with_result(
            name: str,
            success: bool,
            details: list[str],
            output: Path | None,
            payload: dict[str, object],
            retry_attempt: int,
        ) -> int:
            outputs.append({"name": name, "success": success, "details": details, "payload": payload})
            return 0 if success else 1

        args = SimpleNamespace(
            project=ROOT,
            rules=ROOT,
            evidence=None,
            code_review_evidence="reviewed scoped change",
            docs_freshness_evidence="docs unchanged because no durable docs impact",
            structure_review_evidence="",
            boundary_plan_evidence="",
            side_effect_audit_evidence="side-effect audit checked diff; no unexpected changes",
            review_scope="pathspec",
            review_path=["scripts/agent-hook.py"],
            max_changed_paths=25,
            max_source_file_lines=500,
            max_function_lines=120,
            output=None,
            retry_attempt=0,
        )

        result = review_hook(
            args,
            run_command,
            git_status,
            lambda _project, _rules: ["vibeguard", "audit", "."],
            lambda output: "Ready" if "Ready" in output else "unknown",
            finish_with_result,
        )

        self.assertEqual(1, result)
        self.assertFalse(outputs[0]["success"])
        self.assertTrue(
            any("outside the review pathspec" in detail for detail in outputs[0]["details"])
        )

    def test_review_hook_preserves_workflow_validate_diagnostic(self) -> None:
        detail = workflow_validate_failure_detail({
            "returncode": 1,
            "stdout": "",
            "stderr": "Invalid markdown frontmatter:\n- path.md: missing status\n",
        })

        self.assertEqual(
            "workflow validate failed: Invalid markdown frontmatter:; - path.md: missing status",
            detail,
        )

    def test_review_vibeguard_command_uses_pathspec_when_supported(self) -> None:
        calls: list[list[str]] = []

        def run_command(command: list[str], cwd: Path) -> dict[str, object]:
            calls.append(command)
            return {
                "command": command,
                "cwd": str(cwd),
                "returncode": 0,
                "stdout": "usage: vibeguard audit [project] [--path <path>]\n",
                "stderr": "",
            }

        command = review_vibeguard_command(
            ROOT,
            ROOT,
            run_command,
            lambda _project, _rules: ["vibeguard", "audit", ".", "--rules", "."],
            ["scripts/agent_review_hook.py"],
        )

        self.assertEqual(["vibeguard", "--help"], calls[0])
        self.assertEqual(
            [
                "vibeguard",
                "audit",
                ".",
                "--rules",
                ".",
                "--changed-only",
                "--path",
                "scripts/agent_review_hook.py",
            ],
            command(ROOT, ROOT),
        )

    def test_review_vibeguard_command_falls_back_to_changed_only_without_path_support(self) -> None:
        def run_command(command: list[str], cwd: Path) -> dict[str, object]:
            return {
                "command": command,
                "cwd": str(cwd),
                "returncode": 0,
                "stdout": "usage: vibeguard audit [project] [--changed-only]\n",
                "stderr": "",
            }

        command = review_vibeguard_command(
            ROOT,
            ROOT,
            run_command,
            lambda _project, _rules: ["vibeguard", "audit", ".", "--rules", "."],
            ["scripts/agent_review_hook.py"],
        )

        self.assertEqual(
            [
                "vibeguard",
                "audit",
                ".",
                "--rules",
                ".",
                "--changed-only",
            ],
            command(ROOT, ROOT),
        )

    def test_structure_review_warns_for_preexisting_oversized_block_without_growth(self) -> None:
        base_lines = ["def run_import():"]
        base_lines.extend(f"    value_{index} = {index}" for index in range(125))
        base_text = "\n".join(base_lines) + "\n"
        changed_text = base_text.replace("value_50 = 50", "value_50 = 51")

        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source = project / "large.py"
            source.write_text(changed_text, encoding="utf-8")

            def run_command(command: list[str], cwd: Path) -> dict[str, object]:
                if command[:3] == ["git", "rev-parse", "--verify"]:
                    stdout = "abc\n"
                elif command[:3] == ["git", "diff", "--name-status"]:
                    stdout = "M\tlarge.py\n"
                elif command[:3] == ["git", "diff", "--numstat"]:
                    stdout = "1\t1\tlarge.py\n"
                elif command[:2] == ["git", "ls-files"]:
                    stdout = ""
                elif command[:2] == ["git", "show"]:
                    stdout = base_text
                else:
                    stdout = ""
                return {
                    "command": command,
                    "cwd": str(cwd),
                    "returncode": 0,
                    "stdout": stdout,
                    "stderr": "",
                }

            result = structure_review(project, 500, 120, run_command)

        self.assertFalse(any("large.py:1 block `run_import` spans" in failure for failure in result["failures"]))
        self.assertTrue(any("pre-existing oversized unit" in warning for warning in result["warnings"]))

    def test_gate_evidence_ledger_ignores_stale_preflight(self) -> None:
        route = {
            "command": "workflow-setup",
            "docs": ["AGENTS.md"],
            "gates": [CYCLE_CONTRACT_GATE],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "preflight.json"
            preflight = {"route": route}
            evidence_path.write_text(json.dumps(preflight), encoding="utf-8")
            reset_gate_evidence_ledger(evidence_path, preflight)
            record_gate_evidence(
                evidence_path=evidence_path,
                preflight=preflight,
                gate=CYCLE_CONTRACT_GATE,
                fields={
                    "cycle_type": "workflow_setup",
                    "input_scope": "old route",
                    "allowed_changes": "old changes",
                    "forbidden_changes": "old forbidden scope",
                    "acceptance_criteria": "old criteria",
                    "verification": "old verification",
                    "stop_condition": "old stop",
                    "checkpoint": "old checkpoint",
                },
                source="manual",
            )
            stale_preflight = {"route": {**route, "gates": [CYCLE_CONTRACT_GATE, "verify"]}}
            evidence_path.write_text(json.dumps(stale_preflight), encoding="utf-8")

            gate_evidence, diagnostics = merge_gate_evidence_from_ledger(
                route=stale_preflight["route"],
                evidence_path=evidence_path,
                route_docs_receipt={},
                cli_gate_evidence={},
            )

        self.assertEqual({}, gate_evidence)
        self.assertIn("stale", " ".join(diagnostics["warnings"]))

    def test_route_docs_read_evidence_must_match_preflight_doc_manifest(self) -> None:
        route = {
            "gates": [ROUTE_DOCS_READ_GATE],
            "docs": [
                "AGENTS.md",
                "common/skills/agent-operating-skill/SKILL.md",
                "workflows/skills/scripted-agent-workflow/SKILL.md",
            ],
            "required_docs": [
                "AGENTS.md",
                "common/skills/agent-operating-skill/SKILL.md",
            ],
            "reference_docs": [
                "workflows/skills/scripted-agent-workflow/SKILL.md",
            ],
        }

        failures = validate_route_docs_manifest_evidence(
            route,
            {
                ROUTE_DOCS_READ_GATE: (
                    "read routed docs before edits: AGENTS.md and common/skills/agent-operating-skill/SKILL.md"
                )
            },
            {},
        )

        self.assertTrue(any("route docs read receipt is missing" in failure for failure in failures))

        failures = validate_route_docs_manifest_evidence(
            route,
            {ROUTE_DOCS_READ_GATE: "read required docs from the preflight route manifest before edits"},
            {},
        )

        self.assertTrue(any("route docs read receipt is missing" in failure for failure in failures))

        failures = validate_route_docs_manifest_evidence(
            route,
            {ROUTE_DOCS_READ_GATE: "read routed docs before edits with docs-read receipt"},
            {
                "schema_version": 1,
                "route_fingerprint": route_fingerprint(route),
                "doc_count": 2,
                "docs": [
                    {"path": "AGENTS.md", "size_bytes": 1, "sha256": "abc"},
                    {"path": "common/skills/agent-operating-skill/SKILL.md", "size_bytes": 1, "sha256": "def"},
                ],
            },
        )

        self.assertEqual([], failures)
        self.assertEqual(route["required_docs"], route_docs_to_read(route))

    def test_route_docs_read_receipt_rejects_refreshed_preflight_hash(self) -> None:
        route = {
            "gates": [ROUTE_DOCS_READ_GATE],
            "docs": ["AGENTS.md"],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "preflight.json"
            evidence_path.write_text('{"route":"a"}\n', encoding="utf-8")
            receipt = {
                "schema_version": 1,
                "route_fingerprint": route_fingerprint(route),
                "doc_count": 1,
                "preflight_evidence": str(evidence_path),
                "preflight_evidence_sha256": preflight_evidence_sha256(evidence_path),
                "docs": [{"path": "AGENTS.md", "size_bytes": 1, "sha256": "abc"}],
            }

            self.assertEqual(
                [],
                validate_route_docs_manifest_evidence(
                    route,
                    {ROUTE_DOCS_READ_GATE: "read routed docs before edits; applied takeaway: wrapper receipt policy"},
                    receipt,
                    evidence_path,
                ),
            )

            evidence_path.write_text('{"route":"b"}\n', encoding="utf-8")
            failures = validate_route_docs_manifest_evidence(
                route,
                {ROUTE_DOCS_READ_GATE: "read routed docs before edits; applied takeaway: wrapper receipt policy"},
                receipt,
                evidence_path,
            )

        self.assertTrue(any("stale" in failure for failure in failures))

    def test_route_docs_read_receipt_still_binds_to_preflight_evidence_path(self) -> None:
        route = {
            "gates": [ROUTE_DOCS_READ_GATE],
            "docs": ["AGENTS.md"],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            current_evidence = Path(temp_dir) / "current-preflight.json"
            old_evidence = Path(temp_dir) / "old-preflight.json"
            current_evidence.write_text('{"route":"a"}\n', encoding="utf-8")
            old_evidence.write_text('{"route":"a"}\n', encoding="utf-8")
            receipt = {
                "schema_version": 1,
                "route_fingerprint": route_fingerprint(route),
                "doc_count": 1,
                "preflight_evidence": str(old_evidence),
                "preflight_evidence_sha256": preflight_evidence_sha256(old_evidence),
                "docs": [{"path": "AGENTS.md", "size_bytes": 1, "sha256": "abc"}],
            }

            failures = validate_route_docs_manifest_evidence(
                route,
                {ROUTE_DOCS_READ_GATE: "read routed docs before edits; applied takeaway: wrapper receipt policy"},
                receipt,
                current_evidence,
            )

        self.assertTrue(any("different preflight evidence file" in failure for failure in failures))

    def test_docs_read_hook_requires_takeaway_and_next_action(self) -> None:
        route = {
            "command": "workflow-setup",
            "docs": ["AGENTS.md"],
            "gates": [ROUTE_DOCS_READ_GATE],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir).resolve()
            evidence_path = (project / "preflight.json").resolve()
            evidence_path.write_text(json.dumps({"route": route}), encoding="utf-8")

            missing_application = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "agent-hook.py"),
                    "docs-read",
                    "--project",
                    str(project),
                    "--rules",
                    str(ROOT),
                    "--evidence",
                    str(evidence_path),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertNotEqual(0, missing_application.returncode)
            self.assertIn("required recovery", missing_application.stdout)
            self.assertFalse(gate_evidence_path_for_preflight(evidence_path).exists())

            applied_application = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "agent-hook.py"),
                    "docs-read",
                    "--project",
                    str(project),
                    "--rules",
                    str(ROOT),
                    "--evidence",
                    str(evidence_path),
                    "--takeaway",
                    "workflow policy requires actionable required-doc evidence before work",
                    "--next-action",
                    "record the docs-read gate before continuing workflow implementation",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(0, applied_application.returncode, applied_application.stderr)
            receipt = json.loads(
                receipt_path_for_evidence(evidence_path).read_text(encoding="utf-8")
            )
            gate_evidence, diagnostics = merge_gate_evidence_from_ledger(
                route=route,
                evidence_path=evidence_path,
                route_docs_receipt=receipt,
                cli_gate_evidence={},
            )

        self.assertTrue(diagnostics["used"])
        self.assertIn("immediate next action", gate_evidence[ROUTE_DOCS_READ_GATE])

    def test_docs_read_next_action_accepts_concrete_english_and_korean_actions(self) -> None:
        takeaway = "workflow policy requires task-specific action evidence"

        for next_action in (
            "inspect validator callers",
            "run focused tests",
            "현재 저장 경로를 추적해 충돌 지점을 확인한다",
        ):
            with self.subTest(next_action=next_action):
                self.assertEqual(
                    [],
                    validate_route_docs_application_fields(takeaway, next_action),
                )

    def test_docs_read_next_action_rejects_embedded_marker_and_repetition(self) -> None:
        takeaway = "workflow policy requires task-specific action evidence"

        for next_action in (
            "runtime metadata is available",
            "run run run run run",
            "do not run the focused tests",
        ):
            with self.subTest(next_action=next_action):
                self.assertTrue(
                    validate_route_docs_application_fields(takeaway, next_action)
                )

    def test_custom_preflight_gets_isolated_route_docs_receipt_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            self.assertEqual(
                root / "route-docs-read.json",
                receipt_path_for_evidence(root / "preflight.json"),
            )
            self.assertEqual(
                root / "worker-a-route-docs-read.json",
                receipt_path_for_evidence(root / "worker-a.json"),
            )

    def test_finish_can_read_default_receipt_bound_to_custom_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_path = root / "preflight-release-retry.json"
            evidence_path.write_text('{"route":"release"}\n', encoding="utf-8")
            receipt = {
                "schema_version": 1,
                "preflight_evidence": str(evidence_path),
                "preflight_evidence_sha256": preflight_evidence_sha256(evidence_path),
                "route_fingerprint": "abc",
                "doc_count": 0,
                "docs": [],
            }
            (root / "route-docs-read.json").write_text(json.dumps(receipt), encoding="utf-8")

            self.assertEqual(receipt, read_route_docs_receipt_for_preflight(evidence_path))

    def test_prd_and_product_routes_require_alignment_brief(self) -> None:
        prd_route = resolve_docs("prd", None, [], request_classified=True)
        product_route = resolve_docs("product", None, [], request_classified=True)

        self.assertIn(PLATFORM_SELECTION_GATE, product_route["gates"])
        self.assertLess(
            product_route["gates"].index(PLATFORM_SELECTION_GATE),
            product_route["gates"].index("PRD"),
        )
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
        self.assertIn(route_doc("workflows/skills/prd-creation/SKILL.md"), prd_route["docs"])
        self.assertIn(route_doc("workflows/skills/prd-creation/SKILL.md"), product_route["docs"])

    def test_prd_and_spec_routes_get_documentation_enforcement_gates(self) -> None:
        for command in ("prd", "spec"):
            with self.subTest(command=command):
                route = resolve_docs(command, None, [], request_classified=True)

                self.assertIn(SOURCE_DOCS_GATE, route["gates"])
                self.assertIn(DOCUMENTATION_IMPACT_GATE, route["gates"])
                self.assertIn(DOCUMENTATION_GATE, route["gates"])
                self.assertIn(PRD_DRAFT_GATE, route["gates"])
                self.assertLess(
                    route["gates"].index(SOURCE_DOCS_GATE),
                    route["gates"].index("PRD draft"),
                )
                self.assertLess(
                    route["gates"].index(DOCUMENTATION_IMPACT_GATE),
                    route["gates"].index("PRD draft"),
                )
                self.assertLess(
                    route["gates"].index(ALIGNMENT_BRIEF_GATE),
                    route["gates"].index("PRD draft"),
                )
                self.assertLess(
                    route["gates"].index("PRD draft"),
                    route["gates"].index(DOCUMENTATION_GATE),
                )
                self.assertIn(route_doc("workflows/skills/documentation-update/SKILL.md"), route["docs"])

    def test_docs_route_gets_documentation_enforcement_gates(self) -> None:
        route = resolve_docs("docs", None, [], request_classified=True)

        self.assertIn(SOURCE_DOCS_GATE, route["gates"])
        self.assertIn(DOCUMENTATION_IMPACT_GATE, route["gates"])
        self.assertIn(DOCUMENTATION_GATE, route["gates"])
        self.assertLess(route["gates"].index(SOURCE_DOCS_GATE), route["gates"].index("edit"))
        self.assertLess(route["gates"].index(DOCUMENTATION_IMPACT_GATE), route["gates"].index("edit"))
        self.assertIn(route_doc("common/skills/source-driven-development/SKILL.md"), route["docs"])

    def test_prd_draft_evidence_requires_artifact_and_content(self) -> None:
        failures = validate_gate_evidence(
            {PRD_DRAFT_GATE: "PRD draft completed"},
            [PRD_DRAFT_GATE],
        )

        self.assertTrue(any("PRD draft evidence" in failure for failure in failures))

        failures = validate_gate_evidence(
            {PRD_DRAFT_GATE: "discussed acceptance criteria and scope in conversation"},
            [PRD_DRAFT_GATE],
        )

        self.assertTrue(any("PRD draft evidence" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                PRD_DRAFT_GATE: (
                    "created docs/prd-login.md; in scope: login screen; "
                    "acceptance criteria: given valid credentials when submit then navigate home"
                )
            },
            [PRD_DRAFT_GATE],
        )

        self.assertEqual([], failures)

    def test_modify_and_analysis_routes_require_alignment_brief(self) -> None:
        for command in sorted(ALIGNMENT_BRIEF_COMMANDS):
            with self.subTest(command=command):
                route = resolve_docs(command, None, [], request_classified=True)

                self.assertIn(ALIGNMENT_BRIEF_GATE, route["gates"])

    def test_feature_alignment_runs_before_acceptance_criteria(self) -> None:
        route = resolve_docs("feature", None, [], request_classified=True)

        self.assertLess(
            route["gates"].index(ALIGNMENT_BRIEF_GATE),
            route["gates"].index("PRD/ARD applicability"),
        )
        self.assertLess(
            route["gates"].index(ALIGNMENT_BRIEF_GATE),
            route["gates"].index("acceptance criteria"),
        )
        self.assertIn(route_doc("common/skills/task-intake-effort-routing/SKILL.md"), route["docs"])

    def test_grill_me_request_uses_triage_and_grill_gate(self) -> None:
        classification = classify_request("그릴미 해줘")
        route = resolve_docs("triage", None, [], request_classified=True)

        self.assertTrue(classification["grill_me"])
        self.assertTrue(classification["question_drill"])
        self.assertEqual("triage", classification["recommended_route"])
        self.assertIn("grill-me if needed", route["gates"])

    def test_broad_product_request_requires_grill_me_before_work_route(self) -> None:
        classification = classify_request("프로필 설정 기능을 구현해줘")

        self.assertEqual("broad-product", classification["clarity"])
        self.assertEqual("product", classification["recommended_route"])
        self.assertTrue(classification["grill_me"])
        self.assertEqual("clarify_first", classification["response_mode"])
        self.assertIn("needs clarification", route_block_reason("product", classification) or "")
        self.assertIn("Grill-Me", route_block_reason("feature", classification) or "")

    def test_underspecified_action_requires_self_judged_triage(self) -> None:
        classification = classify_request("프로필 저장하고 아바타 프리셋도 추가해줘")

        self.assertEqual("vague-action", classification["clarity"])
        self.assertEqual("triage", classification["recommended_route"])
        self.assertTrue(classification["grill_me"])
        self.assertEqual("clarify_first", classification["response_mode"])
        self.assertIn("lacks a precise target", classification["reason"])

    def test_inspection_request_is_not_blocked_like_product_work(self) -> None:
        classification = classify_request("문서 전체 상태 체크해줘")

        self.assertEqual("clear-scoped", classification["clarity"])
        self.assertEqual("task", classification["recommended_route"])
        self.assertFalse(classification["grill_me"])
        self.assertEqual("work", classification["response_mode"])

    def test_planning_change_doc_omission_request_routes_to_workflow_setup(self) -> None:
        classification = classify_request("기획변경 때 문서 정리가 누락되는 걸 막아줘")

        self.assertEqual("clear-scoped", classification["clarity"])
        self.assertEqual("workflow-setup", classification["recommended_route"])
        self.assertFalse(classification["grill_me"])
        self.assertEqual("work", classification["response_mode"])

    def test_scoped_release_request_routes_without_grill_me(self) -> None:
        classification = classify_request(
            "Deploy Spill macOS app release v2026.28.4 from main HEAD with local "
            "verification, package artifact, tag push, and GitHub Release publication."
        )

        self.assertEqual("clear-scoped", classification["clarity"])
        self.assertEqual("release", classification["recommended_route"])
        self.assertFalse(classification["grill_me"])
        self.assertEqual("work", classification["response_mode"])

    def test_commit_first_release_substep_uses_commit_route(self) -> None:
        classification = classify_request(
            "Commit the current Swift warning cleanup first before continuing the "
            "Spill macOS release sequence."
        )

        self.assertEqual("clear-scoped", classification["clarity"])
        self.assertEqual("commit", classification["recommended_route"])
        self.assertFalse(classification["grill_me"])
        self.assertEqual("work", classification["response_mode"])

    def test_targetless_inspection_request_requires_triage(self) -> None:
        for request in ("확인", "check", "review", "이거 확인해줘"):
            with self.subTest(request=request):
                classification = classify_request(request)

                self.assertEqual("vague-action", classification["clarity"])
                self.assertEqual("triage", classification["recommended_route"])
                self.assertTrue(classification["grill_me"])
                self.assertEqual("clarify_first", classification["response_mode"])

                blocked = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "workflow.py"),
                        "route",
                        "task",
                        "--request",
                        request,
                    ],
                    cwd=str(ROOT),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )

                self.assertEqual(2, blocked.returncode)
                self.assertIn("needs clarification", blocked.stderr)

    def test_grill_me_policy_mention_does_not_require_grill_session(self) -> None:
        classification = classify_request("`scripts/workflow_request.py`의 grill-me skill evidence policy를 수정해줘")

        self.assertFalse(classification["grill_me"])
        self.assertEqual("work", classification["response_mode"])

    def test_grill_me_evidence_requires_protocol_session(self) -> None:
        self.assertEqual(
            [
                "Grill-Me evidence must name the Grill-Me protocol, skill, or /grilling session and its output; "
                "unstructured manual blocker questions alone are not enough"
            ],
            validate_grill_me_skill_evidence("asked blocker questions manually"),
        )
        self.assertEqual(
            [],
            validate_grill_me_skill_evidence(
                "Grill-Me protocol /grilling session output completed: asked one blocker question "
                "with recommended answer and decisions resolved"
            ),
        )

    def test_request_triage_grill_me_output_uses_protocol_session_shape(self) -> None:
        triage_doc = (
            ROOT
            / "workflows"
            / "skills"
            / "request-triage"
            / "references"
            / "current-guidance.md"
        ).read_text()

        self.assertIn("Grill-Me protocol /grilling session", triage_doc)
        self.assertIn("Stop here until the user answers", triage_doc)
        self.assertIn("grill-me if needed=Grill-Me protocol /grilling session output", triage_doc)
        self.assertIn("Do not present a casual clarification question as Grill-Me", triage_doc)

    def test_classification_output_tells_agents_to_start_grilling_session(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "classify",
                "그릴미 해줘",
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Grill-Me protocol: `true`", result.stdout)
        self.assertIn("Start the user-visible clarification with `Grill-Me protocol /grilling session`", result.stdout)
        self.assertIn("grill-me if needed=</grilling session/output evidence>", result.stdout)

    def test_classification_output_includes_model_tier(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "classify",
                "기획변경 때 문서 정리가 누락되는 걸 막아줘",
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Effort: `standard`", result.stdout)
        self.assertIn("Model tier: `balanced`", result.stdout)
        self.assertIn("Codex model: `gpt-5.6-terra`", result.stdout)
        self.assertIn("Runtime mapping: `codex-only-or-runtime-equivalent`", result.stdout)
        self.assertIn("Switching boundary: `task-or-agent-boundary`", result.stdout)

    def test_route_output_includes_model_tier(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "route",
                "workflow-setup",
                "--request",
                "기획변경 때 문서 정리가 누락되는 걸 막아줘",
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("- Effort: `standard`", result.stdout)
        self.assertIn("- Model tier: `balanced`", result.stdout)
        self.assertIn("- Codex model: `gpt-5.6-terra`", result.stdout)
        self.assertIn("- Runtime mapping: `codex-only-or-runtime-equivalent`", result.stdout)
        self.assertIn("- Switching boundary: `task-or-agent-boundary`", result.stdout)

    def test_route_output_tells_agents_to_start_grilling_session(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "route",
                "triage",
                "--request",
                "그릴미 해줘",
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Grill-Me protocol: `true`", result.stdout)
        self.assertIn("Required next action: run a user-visible `Grill-Me protocol /grilling session`", result.stdout)
        self.assertIn("grill-me if needed=</grilling session/output evidence>", result.stdout)

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
        self.assertTrue(any("unstructured manual blocker questions alone are not enough" in failure for failure in failures))

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
        self.assertFalse(any("Grill-Me protocol was required" in failure for failure in failures))

    def test_unresolved_classification_evidence_requires_grill_me_finish_evidence(self) -> None:
        gate_signals: list[dict[str, str]] = []
        missed_gates: list[str] = []
        failures: list[str] = []

        required = check_request_intake(
            {"request_classified": True, "command": "feature"},
            {
                "request_classified": True,
                "classification_evidence": "vague-action clarify_first needs clarification",
            },
            {},
            {},
            gate_signals,
            missed_gates,
            failures,
        )

        self.assertTrue(required)
        self.assertIn("request intake", missed_gates)
        self.assertIn("grill-me", missed_gates)
        self.assertTrue(any("does not prove work can start" in failure for failure in failures))
        self.assertTrue(any("Grill-Me protocol was required" in failure for failure in failures))

    def test_unresolved_direct_question_evidence_fails_request_intake(self) -> None:
        gate_signals: list[dict[str, str]] = []
        missed_gates: list[str] = []
        failures: list[str] = []

        required = check_request_intake(
            {"request_classified": True, "command": "feature"},
            {
                "request_classified": True,
                "classification_evidence": "direct-question answer_first",
            },
            {},
            {},
            gate_signals,
            missed_gates,
            failures,
        )

        self.assertFalse(required)
        self.assertIn("request intake", missed_gates)
        self.assertTrue(any("does not prove work can start" in failure for failure in failures))

    def test_resolved_direct_question_evidence_allows_request_intake(self) -> None:
        gate_signals: list[dict[str, str]] = []
        missed_gates: list[str] = []
        failures: list[str] = []

        required = check_request_intake(
            {"request_classified": True, "command": "feature"},
            {
                "request_classified": True,
                "classification_evidence": (
                    "direct-question answered and separate actionable request remains: "
                    "user asked for review"
                ),
            },
            {},
            {},
            gate_signals,
            missed_gates,
            failures,
        )

        self.assertFalse(required)
        self.assertNotIn("request intake", missed_gates)
        self.assertFalse(any("does not prove work can start" in failure for failure in failures))

    def test_question_resolution_route_allows_unresolved_classification_evidence(self) -> None:
        gate_signals: list[dict[str, str]] = []
        missed_gates: list[str] = []
        failures: list[str] = []

        required = check_request_intake(
            {"request_classified": True, "command": "triage"},
            {
                "request_classified": True,
                "classification_evidence": "vague-action clarify_first needs clarification",
            },
            {},
            {},
            gate_signals,
            missed_gates,
            failures,
        )

        self.assertTrue(required)
        self.assertNotIn("request intake", missed_gates)
        self.assertIn("grill-me", missed_gates)

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
        self.assertTrue(any("Grill-Me protocol was required" in failure for failure in failures))

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
        docs_read_hook = next(hook for hook in route["hooks"] if hook["hook"] == "docs-read")
        review_hook = next(hook for hook in route["hooks"] if hook["hook"] == "review")

        self.assertTrue(docs_read_hook["required"])
        self.assertIn("agent-hook.py docs-read", docs_read_hook["command"])
        self.assertIn("--takeaway", docs_read_hook["command"])
        self.assertIn("--next-action", docs_read_hook["command"])
        self.assertIn("--review-scope working-tree", review_hook["command"])
        self.assertIn("[--review-path <task-owned-path>]", review_hook["command"])
        self.assertIn("--boundary-plan-evidence", review_hook["command"])
        self.assertIn("--side-effect-audit-evidence", review_hook["command"])

    def test_commit_review_hook_command_is_lightweight(self) -> None:
        route = resolve_docs("git_commit", None, [], request_classified=True)
        review_hook = next(hook for hook in route["hooks"] if hook["hook"] == "review")

        self.assertTrue(review_hook["required"])
        self.assertIn("--review-scope working-tree", review_hook["command"])
        self.assertIn("[--review-path <commit-owned-path>]", review_hook["command"])
        self.assertIn("--code-review-evidence", review_hook["command"])
        self.assertIn("--docs-freshness-evidence", review_hook["command"])
        self.assertNotIn("--boundary-plan-evidence", review_hook["command"])
        self.assertNotIn("--side-effect-audit-evidence", review_hook["command"])

    def test_triage_and_ambiguity_read_route_docs_without_code_work_gates(self) -> None:
        for command in ("triage", "ambiguity"):
            with self.subTest(command=command):
                route = resolve_docs(command, None, [], request_classified=True)

                self.assertIn(ROUTE_DOCS_READ_GATE, route["gates"])
                self.assertLess(route["gates"].index(ROUTE_DOCS_READ_GATE), route["gates"].index(ALIGNMENT_BRIEF_GATE))
                self.assertNotIn(TEST_GATE, route["gates"])
                self.assertNotIn(MULTI_AGENT_GATE, route["gates"])

    def test_docs_review_checks_review_readiness(self) -> None:
        route = resolve_docs("docs-review", None, [], request_classified=True)

        self.assertIn(REVIEW_READINESS_GATE, route["gates"])
        self.assertLess(route["gates"].index(REVIEW_READINESS_GATE), route["gates"].index("source review"))

    def test_route_request_classified_requires_evidence(self) -> None:
        missing = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "route",
                "review",
                "--request-classified",
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(2, missing.returncode)
        self.assertIn("--classification-evidence", missing.stderr)

        supplied = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "route",
                "review",
                "--request-classified",
                "--classification-evidence",
                "direct question was answered and user asked for review",
                "--format",
                "json",
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(0, supplied.returncode, supplied.stderr)
        route = json.loads(supplied.stdout)
        self.assertTrue(route["request_classified"])
        self.assertEqual("direct question was answered and user asked for review", route["classification_evidence"])

    def test_request_classified_unresolved_ambiguity_cannot_open_work_route(self) -> None:
        for evidence in (
            "classified",
            "done",
            "vague-action grill_me: true needs clarification",
            "direct-question answer_first",
            "broad-product clarify_first user approved",
            "direct_question answer-first; grill-me true; clarify first",
            "question-drill true",
            "not clarified but clarified",
            "blockers unresolved but clarified",
            "clarified",
            "no blockers",
        ):
            with self.subTest(evidence=evidence):
                blocked = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "workflow.py"),
                        "route",
                        "feature",
                        "--request-classified",
                        "--classification-evidence",
                        evidence,
                    ],
                    cwd=str(ROOT),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )

                self.assertEqual(2, blocked.returncode)
                self.assertIn("does not prove work can start", blocked.stderr)

        base_command = [
            sys.executable,
            str(ROOT / "scripts" / "workflow.py"),
            "route",
        ]
        triage = subprocess.run(
            base_command + [
                "triage",
                "--request-classified",
                "--classification-evidence",
                "vague-action grill_me: true needs clarification",
                "--format",
                "json",
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(0, triage.returncode, triage.stderr)

        for evidence in (
            "clear-scoped workflow policy update",
            "direct question was answered and user asked for review",
            "direct-question answered and separate actionable request remains: user asked for review",
            "vague-action blockers resolved through Grill-Me protocol output",
            "scope clarified after blocker-question protocol",
            "no blockers remain after Grill-Me protocol output",
            "직접 질문 해결 후 별도 작업 요청 남음",
        ):
            with self.subTest(resolved=evidence):
                resolved = subprocess.run(
                    base_command + [
                        "feature",
                        "--request-classified",
                        "--classification-evidence",
                        evidence,
                        "--format",
                        "json",
                    ],
                    cwd=str(ROOT),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )

                self.assertEqual(0, resolved.returncode, resolved.stderr)

    def test_release_classification_evidence_can_use_structured_release_scope(self) -> None:
        evidence = (
            "broad-product clarify_first release scope: Spill macOS app version "
            "v2026.28.4, source revision bc3c4a5, package artifact DMG, tag push "
            "and GitHub Release publication after verification"
        )

        self.assertIsNone(classified_route_block_reason("release", evidence))

        gate_signals: list[dict[str, str]] = []
        missed_gates: list[str] = []
        failures: list[str] = []
        grill_me_required = check_request_intake(
            {"command": "release", "request_classified": True},
            {"request_classified": True, "classification_evidence": evidence},
            {},
            {},
            gate_signals,
            missed_gates,
            failures,
        )

        self.assertFalse(grill_me_required)
        self.assertEqual([], missed_gates)
        self.assertEqual([], failures)

    def test_question_routes_do_not_get_code_work_gates(self) -> None:
        route = resolve_docs("triage", None, [], request_classified=True)

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
                DOCUMENTATION_IMPACT_GATE: "done",
                DOCUMENTATION_GATE: "done",
                SOURCE_DOCS_GATE: "done",
                PLATFORM_SELECTION_GATE: "done",
                REVIEW_READINESS_GATE: "done",
                PRD_DRAFT_GATE: "done",
                TEST_GATE: "done",
                BOUNDARY_PLAN_GATE: "done",
                MULTI_AGENT_GATE: "done",
                AGENTIC_RUN_STATE_GATE: "done",
                SIDE_EFFECT_AUDIT_GATE: "done",
            },
            [
                ROUTE_DOCS_READ_GATE,
                AMBIGUITY_GATE,
                ALIGNMENT_BRIEF_GATE,
                DOCUMENTATION_IMPACT_GATE,
                DOCUMENTATION_GATE,
                SOURCE_DOCS_GATE,
                PLATFORM_SELECTION_GATE,
                REVIEW_READINESS_GATE,
                PRD_DRAFT_GATE,
                TEST_GATE,
                BOUNDARY_PLAN_GATE,
                MULTI_AGENT_GATE,
                AGENTIC_RUN_STATE_GATE,
                SIDE_EFFECT_AUDIT_GATE,
            ],
        )

        self.assertEqual(14, len(failures))

    def test_required_gate_skip_evidence_fails_unless_gate_allows_skip(self) -> None:
        failures = validate_gate_evidence(
            {
                BOUNDARY_PLAN_GATE: "skipped because this looked small",
            },
            [BOUNDARY_PLAN_GATE],
        )

        self.assertTrue(any("cannot pass by recording a skip" in failure for failure in failures))

        allowed = validate_gate_evidence(
            {
                TEST_GATE: "tests not run because docs-only change has no useful test",
            },
            [TEST_GATE],
        )

        self.assertEqual([], allowed)

    def test_required_gate_skip_guard_ignores_policy_implementation_language(self) -> None:
        failures = validate_gate_evidence(
            {
                BOUNDARY_PLAN_GATE: (
                    "boundary/scope: finish-check skip validation policy; nearest "
                    "verification/check: unit tests and workflow validate covered the "
                    "gate evidence validator"
                )
            },
            [BOUNDARY_PLAN_GATE],
        )

        self.assertEqual([], failures)

        failures = validate_gate_evidence(
            {
                CYCLE_CONTRACT_GATE: (
                    "cycle_type=workflow_setup; input_scope=gate evidence policy; "
                    "allowed_changes=finish-check validator tests; "
                    "forbidden_changes=unrelated behavior; "
                    "acceptance criteria=required gates fail on real skipped or "
                    "deferred fixes; verification=unit tests; "
                    "stop condition=policy language does not count as a gate skip; "
                    "checkpoint=finish"
                )
            },
            [CYCLE_CONTRACT_GATE],
        )

        self.assertEqual([], failures)

    def test_required_gate_skip_guard_allows_non_skip_unable_language(self) -> None:
        failures = validate_gate_evidence(
            {
                BOUNDARY_PLAN_GATE: (
                    "boundary/scope: regression reproduction notes; nearest "
                    "verification/check: unable to reproduce further edge cases "
                    "after unit tests and workflow validate"
                )
            },
            [BOUNDARY_PLAN_GATE],
        )

        self.assertEqual([], failures)

    def test_required_gate_skip_guard_allows_scoped_review_caveat(self) -> None:
        failures = validate_gate_evidence(
            {
                SIDE_EFFECT_AUDIT_GATE: (
                    "side-effect audit checked final diff; scope/risk reviewed: "
                    "not reviewed by a second person but self-tested with focused "
                    "unit coverage; result: no side effects found"
                )
            },
            [SIDE_EFFECT_AUDIT_GATE],
        )

        self.assertEqual([], failures)

    def test_required_gate_skip_guard_blocks_explicit_not_applicable_required_gate(self) -> None:
        failures = validate_gate_evidence(
            {
                BOUNDARY_PLAN_GATE: (
                    "not applicable because this change looked small"
                )
            },
            [BOUNDARY_PLAN_GATE],
        )

        self.assertTrue(any("cannot pass by recording a skip" in failure for failure in failures))

    def test_required_gate_unresolved_issue_evidence_fails(self) -> None:
        failures = validate_gate_evidence(
            {
                SIDE_EFFECT_AUDIT_GATE: (
                    "side-effect audit checked diff; public api risk found, should fix later"
                ),
            },
            [SIDE_EFFECT_AUDIT_GATE],
        )

        self.assertTrue(any("unresolved issue" in failure for failure in failures))

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

    def test_alignment_evidence_accepts_choice_question_checkpoint(self) -> None:
        failures = validate_gate_evidence(
            {
                ALIGNMENT_BRIEF_GATE: (
                    "same understanding: rewrite requested; possible differences: genre and point of view; "
                    "unsupported assumptions: style cue alone does not choose retrospective mode; "
                    "choice question presented before edits"
                )
            },
            [ALIGNMENT_BRIEF_GATE],
        )

        self.assertEqual([], failures)

    def test_finish_policy_accepts_specific_evidence(self) -> None:
        failures = validate_gate_evidence(
            {
                ROUTE_DOCS_READ_GATE: (
                    "read routed docs before code: AGENTS.md, index.md, "
                    "common/skills/agent-operating-skill/SKILL.md; applied takeaway: wrapper "
                    "receipt policy and gate evidence criteria; immediate next action: "
                    "record structured gate evidence before continuing implementation"
                ),
                AMBIGUITY_GATE: "no blockers; safe assumption recorded",
                ALIGNMENT_BRIEF_GATE: (
                    "same understanding: explicit goal captured; possible differences: uncertain scope; "
                    "unsupported assumptions: default MVP unless blocker question changes it; "
                    "user-visible checkpoint told the user before edits"
                ),
                DOCUMENTATION_IMPACT_GATE: (
                    "before implementation documentation impact decision: "
                    "artifact: workflow card; update workflows/README.md because workflow policy changed"
                ),
                DOCUMENTATION_GATE: (
                    "updated workflows/README.md because workflow policy changed; "
                    "source-of-truth updated for durable agent behavior"
                ),
                SOURCE_DOCS_GATE: (
                    "searched PRD/spec/ARD source-of-truth docs before implementation; "
                    "none found; used user request as source of truth"
                ),
                PLATFORM_SELECTION_GATE: (
                    "selected platform: ios; loaded platforms/ios/skills/ios-architecture/SKILL.md "
                    "before PRD/ARD architecture work"
                ),
                REVIEW_READINESS_GATE: (
                    "review readiness checked markdown frontmatter status/type counts; "
                    "human-reviewed-needed review queue found"
                ),
                PRD_DRAFT_GATE: (
                    "created docs/prd-login.md; in scope: login screen with email/password; "
                    "acceptance criteria: given valid credentials when submit then navigate home"
                ),
                TEST_GATE: "unittest tests/test_workflow_routing.py passed",
                BOUNDARY_PLAN_GATE: "existing workflow gate policy boundary; verification via unittest",
                MULTI_AGENT_GATE: (
                    "no subagent split: serial single-agent because small same-file policy change "
                    "with same-file scope"
                ),
                AGENTIC_RUN_STATE_GATE: (
                    "run state: scoped; next transition: scoped -> acting; "
                    "evidence: boundary gate and unittest verification command recorded; "
                    "checkpoint: implementation handoff; blocker status: no blockers"
                ),
                SIDE_EFFECT_AUDIT_GATE: "final diff checked; no unexpected generated files or lockfile changes",
            },
            [
                ROUTE_DOCS_READ_GATE,
                AMBIGUITY_GATE,
                ALIGNMENT_BRIEF_GATE,
                DOCUMENTATION_IMPACT_GATE,
                DOCUMENTATION_GATE,
                SOURCE_DOCS_GATE,
                PLATFORM_SELECTION_GATE,
                REVIEW_READINESS_GATE,
                PRD_DRAFT_GATE,
                TEST_GATE,
                BOUNDARY_PLAN_GATE,
                MULTI_AGENT_GATE,
                AGENTIC_RUN_STATE_GATE,
                SIDE_EFFECT_AUDIT_GATE,
            ],
        )

        self.assertEqual([], failures)

    def test_source_docs_evidence_requires_source_artifact_discovery_before_work(self) -> None:
        failures = validate_gate_evidence(
            {SOURCE_DOCS_GATE: "checked docs"},
            [SOURCE_DOCS_GATE],
        )

        self.assertTrue(any("source-of-truth docs" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                SOURCE_DOCS_GATE: (
                    "searched source-of-truth docs before implementation; "
                    "found docs/module/README.md and read it; applied module boundary to the work"
                )
            },
            [SOURCE_DOCS_GATE],
        )

        self.assertEqual([], failures)

    def test_platform_selection_evidence_requires_platform_or_not_applicable_reason(self) -> None:
        failures = validate_gate_evidence(
            {PLATFORM_SELECTION_GATE: "done"},
            [PLATFORM_SELECTION_GATE],
        )

        self.assertTrue(any("platform selection evidence" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                PLATFORM_SELECTION_GATE: (
                    "selected platform: web; loaded platforms/web/skills/web-architecture/SKILL.md "
                    "before PRD/ARD architecture work"
                )
            },
            [PLATFORM_SELECTION_GATE],
        )

        self.assertEqual([], failures)

        failures = validate_gate_evidence(
            {
                PLATFORM_SELECTION_GATE: (
                    "not applicable because workflow-only docs change has no platform-specific runtime"
                )
            },
            [PLATFORM_SELECTION_GATE],
        )

        self.assertEqual([], failures)

    def test_review_readiness_evidence_requires_status_type_queue(self) -> None:
        failures = validate_gate_evidence(
            {REVIEW_READINESS_GATE: "checked docs"},
            [REVIEW_READINESS_GATE],
        )

        self.assertTrue(any("review readiness evidence" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                REVIEW_READINESS_GATE: (
                    "review readiness checked markdown frontmatter status/type counts; "
                    "human-reviewed-needed review queue found under common/ and workflows/"
                )
            },
            [REVIEW_READINESS_GATE],
        )

        self.assertEqual([], failures)

    def test_documentation_evidence_requires_target_and_reason(self) -> None:
        failures = validate_gate_evidence(
            {DOCUMENTATION_GATE: "updated docs"},
            [DOCUMENTATION_GATE],
        )

        self.assertTrue(any("documentation decision" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                DOCUMENTATION_GATE: (
                    "updated docs/prd.md because acceptance criteria changed; "
                    "source-of-truth updated for durable behavior"
                )
            },
            [DOCUMENTATION_GATE],
        )

        self.assertEqual([], failures)

    def test_documentation_impact_evidence_requires_pre_edit_decision(self) -> None:
        failures = validate_gate_evidence(
            {DOCUMENTATION_IMPACT_GATE: "will think about docs later"},
            [DOCUMENTATION_IMPACT_GATE],
        )

        self.assertTrue(any("documentation impact evidence" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                DOCUMENTATION_IMPACT_GATE: (
                    "before code documentation impact decision: artifact: workflow card; "
                    "update workflows/README.md because workflow policy changed"
                )
            },
            [DOCUMENTATION_IMPACT_GATE],
        )

        self.assertEqual([], failures)

    def test_documentation_impact_rejects_non_creation_without_no_durable_reason(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_IMPACT_GATE: (
                    "before code documentation impact decision: artifact: feature spec; "
                    "not applicable because new feature changed behavior"
                )
            },
            [DOCUMENTATION_IMPACT_GATE],
        )

        self.assertTrue(any("cannot use not-applicable/no-docs" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                DOCUMENTATION_IMPACT_GATE: (
                    "before code documentation impact decision: artifact: feature spec; "
                    "not applicable because answer-only with no durable behavior"
                )
            },
            [DOCUMENTATION_IMPACT_GATE],
        )

        self.assertEqual([], failures)

    def test_documentation_impact_rejects_no_docs_for_requirements_change(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_IMPACT_GATE: (
                    "before code documentation impact decision: artifact: feature spec; "
                    "not applicable because no public contract, but requirements changed "
                    "the acceptance criteria"
                )
            },
            [DOCUMENTATION_IMPACT_GATE],
        )

        self.assertTrue(any("cannot use not-applicable/no-docs" in failure for failure in failures))

    def test_documentation_impact_allows_unchanged_when_existing_doc_covers_change(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_IMPACT_GATE: (
                    "before code documentation impact decision: artifact: feature spec; "
                    "unchanged docs/product/spec.md; inspected the existing doc and it "
                    "already covers the revised acceptance criteria"
                )
            },
            [DOCUMENTATION_IMPACT_GATE],
        )

        self.assertEqual([], failures)

    def test_documentation_impact_rejects_unchanged_without_inspection_proof(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_IMPACT_GATE: (
                    "before code documentation impact decision: artifact: feature spec; "
                    "unchanged docs/product/spec.md because it already covers the "
                    "revised acceptance criteria"
                )
            },
            [DOCUMENTATION_IMPACT_GATE],
        )

        self.assertTrue(any("can use unchanged only" in failure for failure in failures))

    def test_documentation_impact_rejects_vague_unchanged_decision(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_IMPACT_GATE: (
                    "before code documentation impact decision: artifact: feature spec; "
                    "unchanged because requirements changed"
                )
            },
            [DOCUMENTATION_IMPACT_GATE],
        )

        self.assertTrue(any("can use unchanged only" in failure for failure in failures))

    def test_documentation_gate_rejects_no_docs_for_requirements_change(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_GATE: (
                    "not applicable for docs/product/spec.md because no public contract, "
                    "but requirements changed the acceptance criteria"
                )
            },
            [DOCUMENTATION_GATE],
        )

        self.assertTrue(any("cannot use not-applicable/no-docs" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                DOCUMENTATION_GATE: (
                    "unchanged docs/product/spec.md; inspected it and the existing doc "
                    "already covers the revised acceptance criteria"
                )
            },
            [DOCUMENTATION_GATE],
        )

        self.assertEqual([], failures)

    def test_documentation_gate_rejects_unchanged_without_inspection_proof(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_GATE: (
                    "unchanged docs/product/spec.md because it already covers the "
                    "revised acceptance criteria"
                )
            },
            [DOCUMENTATION_GATE],
        )

        self.assertTrue(any("can use unchanged only" in failure for failure in failures))

    def test_documentation_gate_rejects_unchanged_without_named_doc_path(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_GATE: (
                    "unchanged; inspected the module readme and it already covers "
                    "the acceptance criteria"
                )
            },
            [DOCUMENTATION_GATE],
        )

        self.assertTrue(any("can use unchanged only" in failure for failure in failures))

    def test_required_documentation_gate_rejects_empty_evidence(self) -> None:
        failures = validate_gate_evidence(
            {DOCUMENTATION_GATE: ""},
            [DOCUMENTATION_GATE],
        )

        self.assertTrue(
            any("required and cannot be empty" in failure for failure in failures)
        )

    def test_documentation_skip_requires_user_approval_not_reason(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_GATE: (
                    "documentation decision: not applicable; target: module README; "
                    "reason: answer-only with no durable behavior"
                )
            },
            [DOCUMENTATION_GATE],
        )

        self.assertTrue(any("cannot be skipped" in failure for failure in failures))

    def test_documentation_skipped_phrase_requires_user_approval(self) -> None:
        failures = validate_gate_evidence(
            {DOCUMENTATION_GATE: "documentation skipped because the change was trivial"},
            [DOCUMENTATION_GATE],
        )

        self.assertTrue(any("cannot be skipped" in failure for failure in failures))

    def test_documentation_skip_passes_with_recorded_user_approval(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_GATE: (
                    "documentation decision: not applicable; target: module README; "
                    "reason: answer-only; asked the user 문서를 스킵할까요 and the user "
                    "approved skipping the doc"
                )
            },
            [DOCUMENTATION_GATE],
        )

        self.assertEqual([], failures)

    def test_documentation_skip_does_not_pass_when_user_was_only_asked(self) -> None:
        failures = validate_gate_evidence(
            {
                DOCUMENTATION_GATE: (
                    "documentation decision: not applicable; target: module README; "
                    "reason: answer-only; asked the user whether to skip the doc but "
                    "no approval was received"
                )
            },
            [DOCUMENTATION_GATE],
        )

        self.assertTrue(any("cannot be skipped" in failure for failure in failures))

    def test_triage_and_plan_routes_get_product_reentry_gate(self) -> None:
        for command in sorted(PRODUCT_REENTRY_COMMANDS):
            with self.subTest(command=command):
                route = resolve_docs(command, None, [], request_classified=True)
                self.assertIn(PRODUCT_REENTRY_GATE, route["gates"])

    def test_product_reentry_gate_requires_non_empty_evidence(self) -> None:
        failures = validate_gate_evidence(
            {PRODUCT_REENTRY_GATE: ""},
            [PRODUCT_REENTRY_GATE],
        )

        self.assertTrue(
            any("required and cannot be empty" in failure for failure in failures)
        )

    def test_product_reentry_gate_allows_no_implementation_proposed(self) -> None:
        failures = validate_gate_evidence(
            {
                PRODUCT_REENTRY_GATE: (
                    "recommendation only; no implementation proposed, this triage "
                    "stayed at status and classification"
                )
            },
            [PRODUCT_REENTRY_GATE],
        )

        self.assertEqual([], failures)

    def test_product_reentry_gate_rejects_roadmap_without_prd_coverage(self) -> None:
        failures = validate_gate_evidence(
            {
                PRODUCT_REENTRY_GATE: (
                    "proposed an implementation roadmap with three milestones and a "
                    "task list for the next feature"
                )
            },
            [PRODUCT_REENTRY_GATE],
        )

        self.assertTrue(any("PRD coverage" in failure for failure in failures))

    def test_product_reentry_gate_allows_roadmap_with_prd_coverage(self) -> None:
        failures = validate_gate_evidence(
            {
                PRODUCT_REENTRY_GATE: (
                    "proposed implementation roadmap; re-enter product route and map "
                    "each item to an Accepted PRD link, with an ARD link for module "
                    "boundary changes, before any implementation task or PR"
                )
            },
            [PRODUCT_REENTRY_GATE],
        )

        self.assertEqual([], failures)

    def test_product_reentry_gate_rejects_acceptance_criteria_without_prd(self) -> None:
        failures = validate_gate_evidence(
            {
                PRODUCT_REENTRY_GATE: (
                    "proposed an implementation roadmap with acceptance criteria for "
                    "each milestone"
                )
            },
            [PRODUCT_REENTRY_GATE],
        )

        self.assertTrue(any("PRD coverage" in failure for failure in failures))

    def test_product_reentry_gate_rejects_ard_link_without_prd(self) -> None:
        failures = validate_gate_evidence(
            {
                PRODUCT_REENTRY_GATE: (
                    "proposed an implementation roadmap with an ARD link for module "
                    "boundaries"
                )
            },
            [PRODUCT_REENTRY_GATE],
        )

        self.assertTrue(any("PRD coverage" in failure for failure in failures))

    def test_missing_source_docs_requires_artifact_creation_or_no_durable_reason(self) -> None:
        failures = validate_gate_evidence(
            {
                SOURCE_DOCS_GATE: (
                    "searched PRD/spec/ARD source-of-truth docs before implementation; "
                    "none found; used user request as source of truth"
                ),
                DOCUMENTATION_IMPACT_GATE: (
                    "before code documentation impact decision: artifact: module README; "
                    "not applicable because new module changed behavior"
                ),
            },
            [SOURCE_DOCS_GATE, DOCUMENTATION_IMPACT_GATE],
        )

        self.assertTrue(any("when source docs are missing" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                SOURCE_DOCS_GATE: (
                    "searched PRD/spec/ARD source-of-truth docs before implementation; "
                    "none found; used user request as source of truth"
                ),
                DOCUMENTATION_IMPACT_GATE: (
                    "before code documentation impact decision: artifact: module README; "
                    "create docs/module/README.md because new module behavior changed"
                ),
            },
            [SOURCE_DOCS_GATE, DOCUMENTATION_IMPACT_GATE],
        )

        self.assertEqual([], failures)

    def test_route_docs_read_evidence_requires_applied_takeaway(self) -> None:
        failures = validate_gate_evidence(
            {ROUTE_DOCS_READ_GATE: "read routed docs before edits with docs-read receipt"},
            [ROUTE_DOCS_READ_GATE],
        )

        self.assertTrue(any("applied" in failure for failure in failures))

    def test_route_docs_read_evidence_requires_immediate_next_action(self) -> None:
        failures = validate_gate_evidence(
            {
                ROUTE_DOCS_READ_GATE: (
                    "read routed docs before edits with docs-read receipt; "
                    "applied takeaway: wrapper receipt policy and gate evidence criteria"
                )
            },
            [ROUTE_DOCS_READ_GATE],
        )

        self.assertTrue(any("immediate next action" in failure for failure in failures))

    def test_route_docs_read_evidence_allows_commit_before_work_terms(self) -> None:
        failures = validate_gate_evidence(
            {
                ROUTE_DOCS_READ_GATE: (
                    "required skill docs read before committing; "
                    "applied rule: one commit should carry one reviewable intent; "
                    "immediate next action: commit the staged graphify artifact unit"
                )
            },
            [ROUTE_DOCS_READ_GATE],
        )

        self.assertEqual([], failures)

    def test_route_docs_read_evidence_rejects_receipt_only_takeaway(self) -> None:
        route = {
            "command": "workflow-setup",
            "docs": ["AGENTS.md"],
            "gates": [ROUTE_DOCS_READ_GATE],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            evidence_path = Path(temp_dir) / "preflight.json"
            preflight = {"route": route}
            evidence_path.write_text(json.dumps(preflight), encoding="utf-8")
            reset_gate_evidence_ledger(evidence_path, preflight)

            record_gate_evidence(
                evidence_path=evidence_path,
                preflight=preflight,
                gate=ROUTE_DOCS_READ_GATE,
                fields={
                    "takeaway": "route docs receipt matched the current preflight manifest",
                    "next_action": "continue by editing the scoped workflow hook",
                },
                source="docs-read",
            )
            receipt = {
                "schema_version": 1,
                "route_fingerprint": route_fingerprint(route),
                "doc_count": 1,
                "preflight_evidence": str(evidence_path),
                "preflight_evidence_sha256": preflight_evidence_sha256(evidence_path),
                "docs": [{"path": "AGENTS.md", "size_bytes": 1, "sha256": "abc"}],
            }

            gate_evidence, diagnostics = merge_gate_evidence_from_ledger(
                route=route,
                evidence_path=evidence_path,
                route_docs_receipt=receipt,
                cli_gate_evidence={},
            )

        self.assertEqual({}, gate_evidence)
        self.assertIn(ROUTE_DOCS_READ_GATE, diagnostics["missing_fields"])
        self.assertTrue(any("task-specific" in item for item in diagnostics["missing_fields"][ROUTE_DOCS_READ_GATE]))

    def test_parallel_subagent_evidence_requires_contract_forbidden_scope_and_verification(self) -> None:
        failures = validate_gate_evidence(
            {MULTI_AGENT_GATE: "parallel subagent split with owned scope"},
            [MULTI_AGENT_GATE],
        )

        self.assertTrue(any("acceptance checks, integration owner, and verification" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                MULTI_AGENT_GATE: (
                    "parallel subagent split: worker docs owns workflows/*.md; "
                    "forbidden scope: scripts/*.py; contract brief: report only doc gaps; "
                    "acceptance checks: findings include file and rule; "
                    "integration owner: lead agent; verification: workflow validate"
                )
            },
            [MULTI_AGENT_GATE],
        )

        self.assertEqual([], failures)

    def test_parallel_subagent_evidence_requires_acceptance_and_integration_owner(self) -> None:
        failures = validate_gate_evidence(
            {
                MULTI_AGENT_GATE: (
                    "parallel subagent split: worker docs owns workflows/*.md; "
                    "forbidden scope: scripts/*.py; contract brief: report only doc gaps; "
                    "verification: workflow validate"
                )
            },
            [MULTI_AGENT_GATE],
        )

        self.assertTrue(any("acceptance checks, integration owner" in failure for failure in failures))

    def test_parallel_subagent_finish_requires_structured_delegation_plan(self) -> None:
        evidence = {
            MULTI_AGENT_GATE: (
                "parallel subagent split: worker docs owns workflows/*.md; "
                "forbidden scope: scripts/*.py; contract brief: report doc gaps; "
                "acceptance checks: findings include file and rule; "
                "integration owner: lead agent; verification: workflow validate"
            )
        }

        failures = validate_delegation_plan_evidence([MULTI_AGENT_GATE], evidence, {})

        self.assertTrue(any("agent-delegation-plan.json" in failure for failure in failures))

        plan = {
            "schema_version": 1,
            "mode": "parallel",
            "workers": [
                {
                    "id": "docs-a",
                    "role": "docs reviewer",
                    "owned_scope": ["workflows/*.md"],
                    "forbidden_scope": ["scripts/*.py"],
                    "contract": "report documentation gaps only",
                    "acceptance": ["findings include file and rule"],
                    "verification": ["python3 scripts/workflow.py validate"],
                }
            ],
            "integration_review": {
                "owner": "lead agent",
                "contract_drift_check": "compare worker findings with route gate policy",
                "final_verification": ["python3 -m unittest discover tests"],
            },
        }

        self.assertEqual([], validate_delegation_plan_evidence([MULTI_AGENT_GATE], evidence, plan))

    def test_parallel_delegation_plan_requires_integration_owner(self) -> None:
        evidence = {
            MULTI_AGENT_GATE: (
                "parallel subagent split: worker docs owns workflows/*.md; "
                "forbidden scope: scripts/*.py; contract brief: report doc gaps; "
                "acceptance checks: findings include file and rule; "
                "integration owner: lead agent; verification: workflow validate"
            )
        }
        plan = {
            "schema_version": 1,
            "mode": "parallel",
            "workers": [
                {
                    "id": "docs-a",
                    "role": "docs reviewer",
                    "owned_scope": ["workflows/*.md"],
                    "forbidden_scope": ["scripts/*.py"],
                    "contract": "report documentation gaps only",
                    "acceptance": ["findings include file and rule"],
                    "verification": ["python3 scripts/workflow.py validate"],
                }
            ],
            "integration_review": {
                "contract_drift_check": "compare worker findings with route gate policy",
                "final_verification": ["python3 -m unittest discover tests"],
            },
        }

        failures = validate_delegation_plan_evidence([MULTI_AGENT_GATE], evidence, plan)

        self.assertTrue(any("owner/integration_owner" in failure for failure in failures))

    def test_serial_multi_agent_decision_does_not_require_delegation_plan(self) -> None:
        failures = validate_delegation_plan_evidence(
            [MULTI_AGENT_GATE],
            {
                MULTI_AGENT_GATE: (
                    "serial single-agent because same-file contract-bound change with overlapping verification"
                )
            },
            {},
        )

        self.assertEqual([], failures)

    def test_multi_agent_route_specific_gates_require_structured_delegation_plan(self) -> None:
        failures = validate_delegation_plan_evidence(
            ["roles", "write scopes", "agent briefs", "integration review"],
            {},
            {},
        )

        self.assertTrue(any("agent-delegation-plan.json" in failure for failure in failures))

    def test_multi_agent_route_gates_reject_done_only_evidence(self) -> None:
        failures = validate_gate_evidence(
            {
                "roles": "done",
                "write scopes": "done",
                "agent briefs": "done",
                "integration review": "done",
            },
            ["roles", "write scopes", "agent briefs", "integration review"],
        )

        self.assertEqual(4, len(failures))

    def test_multi_agent_route_gates_accept_specific_delegation_evidence(self) -> None:
        failures = validate_gate_evidence(
            {
                "roles": "lead owner: main agent; worker: docs verifier; verifier: main review",
                "write scopes": "owned write scope: workflows/*.md; forbidden/read-only scope: scripts/*.py",
                "agent briefs": (
                    "worker docs-a role verifier; owned scope workflows/*.md; forbidden scope scripts/*.py; "
                    "input contract route docs policy; expected output findings; acceptance checks listed; "
                    "verification: workflow validate"
                ),
                "integration review": (
                    "integration review after merge; contract drift check for route/schema/state model; "
                    "final verification: unittest and workflow validate"
                ),
            },
            ["roles", "write scopes", "agent briefs", "integration review"],
        )

        self.assertEqual([], failures)

    def test_agentic_run_state_evidence_requires_state_transition_and_evidence(self) -> None:
        failures = validate_gate_evidence(
            {AGENTIC_RUN_STATE_GATE: "state: scoped"},
            [AGENTIC_RUN_STATE_GATE],
        )

        self.assertTrue(any("agentic run state evidence" in failure for failure in failures))

        failures = validate_gate_evidence(
            {
                AGENTIC_RUN_STATE_GATE: (
                    "run state: reviewing; next transition: reviewing -> done; "
                    "evidence: review hook and validation check passed; "
                    "checkpoint: final handoff; blocker status: no blockers"
                )
            },
            [AGENTIC_RUN_STATE_GATE],
        )

        self.assertEqual([], failures)

    def test_agentic_run_state_evidence_requires_checkpoint_and_blocker_status(self) -> None:
        failures = validate_gate_evidence(
            {
                AGENTIC_RUN_STATE_GATE: (
                    "run state: reviewing; next transition: reviewing -> done; "
                    "evidence: review hook and validation check passed"
                )
            },
            [AGENTIC_RUN_STATE_GATE],
        )

        self.assertTrue(any("checkpoint or stop condition" in failure for failure in failures))


class BaselineEnforcementStaysCentralTest(unittest.TestCase):
    """The gate rules live once in the canonical skill; the per-repo stamp is a
    pointer, never a duplicated rule block."""

    def _read(self, *parts: str) -> str:
        return (ROOT.joinpath(*parts)).read_text(encoding="utf-8")

    def test_stamp_template_is_pointer_not_duplicated_rules(self) -> None:
        template = self._read("templates", "repo-agents-routing.md")
        self.assertIn("workflows/skills/documentation-update/SKILL.md", template)
        self.assertIn("Do not duplicate or restate", template)
        # The full rule prose (the skip question) belongs only in the canonical
        # skill, not re-inlined into every stamped repo.
        self.assertNotIn("문서를 스킵할까요", template)

    def test_canonical_skill_holds_the_full_rules_and_centralization(self) -> None:
        skill = self._read(
            "workflows", "skills", "documentation-update", "references", "current-guidance.md"
        )
        self.assertIn("문서를 스킵할까요", skill)
        self.assertIn("Where the rules live", skill)


if __name__ == "__main__":
    unittest.main()
