from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_finish_gate_policy import (
    PLATFORM_SELECTION_GATE,
    PRD_DRAFT_GATE,
    REVIEW_READINESS_GATE,
    VALIDATED_GATES,
    validate_gate_evidence,
)
from agent_finish_check_steps import (
    check_request_intake,
    validate_grill_me_skill_evidence,
    validate_route_docs_manifest_evidence,
)
from agent_gate_evidence import (
    gate_evidence_path_for_preflight,
    merge_gate_evidence_from_ledger,
    record_gate_evidence,
    reset_gate_evidence_ledger,
)
from agent_delegation_plan import validate_delegation_plan_evidence
from agent_global_lessons import lesson_summary, write_retrospective_candidate
from agent_preflight_runtime import (
    AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES as PREFLIGHT_AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES,
    _claude_spill_warnings,
)
from agent_route_docs import preflight_evidence_sha256, route_fingerprint
from support.agy_setup import AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES, _agy_runtime_bridge_block
from support.claude_setup import _CLASSIFICATION_EVIDENCE, _merge_claude_user_prompt_submit
from support.permission_entries import agy_permission_entries, claude_permission_entries, codex_prefix_rule_entries
from support.stable_launcher import stable_launcher_path
from workflow_catalog import COMMANDS, CONCERNS
from workflow_gate_policy import (
    AGENTIC_RUN_STATE_GATE,
    AMBIGUITY_GATE,
    ALIGNMENT_BRIEF_GATE,
    BOUNDARY_PLAN_GATE,
    CYCLE_CONTRACT_GATE,
    DOCUMENTATION_IMPACT_GATE,
    DOCUMENTATION_GATE,
    MULTI_AGENT_GATE,
    ROUTE_DOCS_READ_GATE,
    SIDE_EFFECT_AUDIT_GATE,
    SOURCE_DOCS_GATE,
    TEST_GATE,
    ALIGNMENT_BRIEF_COMMANDS,
    WORK_PRODUCING_COMMANDS,
)
from workflow_request import infer_concerns_from_request
from workflow_request import classify_request
from workflow_request import route_block_reason
from workflow_parallel_validate import validate_parallel_execution_plan
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
        self.assertIn("common/scenario-driven-testing.md", CONCERNS["testing"])
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

        test_route = resolve_docs("test", None, [], request_classified=True)
        self.assertIn("common/scenario-driven-testing.md", test_route["docs"])

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

    def test_web_deployment_versioning_routes_with_release_and_shipping(self) -> None:
        doc = "common/web-deployment-versioning.md"

        self.assertIn(doc, CONCERNS["release"])
        self.assertIn(doc, CONCERNS["shipping"])
        self.assertIn(doc, resolve_docs("docs", "web", ["release"], request_classified=True)["docs"])
        self.assertIn(doc, resolve_docs("ship", "web", ["shipping"], request_classified=True)["docs"])

        examples = (
            "Define web deployment versioning for every main merge",
            "Should web deploys bump SemVer or use deployment ids?",
            "웹 배포 버전 체계를 정리해줘",
        )
        for request in examples:
            with self.subTest(request=request):
                self.assertIn("release", infer_concerns_from_request(request))

    def test_credential_broker_concern_routes_to_product_pattern(self) -> None:
        doc = "product-patterns/agent-credential-broker-ideation.md"
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
        self.assertIn(doc, route["docs"])

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
                self.assertIn("common/accessibility-i18n.md", CONCERNS[concern])

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
        self.assertIn("common/accessibility-i18n.md", route["docs"])

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

    def test_android_persistence_route_loads_datastore_reference(self) -> None:
        for concern in ("persistence", "cache"):
            with self.subTest(concern=concern):
                route = resolve_docs(
                    "feature",
                    "android",
                    [concern],
                    request_classified=True,
                )

                self.assertIn("platforms/android/android-state-data.md", route["docs"])
                self.assertIn("platforms/android/references/android-datastore.md", route["docs"])

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

        self.assertIn("workflows/ambiguity-gate.md", route["docs"])
        self.assertIn("workflows/documentation-update.md", route["docs"])
        self.assertIn("common/product-spec-to-implementation.md", route["docs"])
        self.assertIn("common/source-driven-development.md", route["docs"])
        self.assertIn("common/testing.md", route["docs"])
        self.assertIn("common/scenario-driven-testing.md", route["docs"])
        self.assertIn("common/verification-policy.md", route["docs"])
        self.assertIn("common/code-structure-ownership.md", route["docs"])
        self.assertIn("workflows/cycle-contract.md", route["docs"])
        self.assertIn("workflows/multi-agent-collaboration.md", route["docs"])
        self.assertIn("workflows/development-cycle.md", route["docs"])
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
        self.assertEqual("conditional_parallel", phases["worker_execution"]["mode"])
        self.assertIn("roles", phases["worker_execution"]["gates"])
        self.assertIn("write scopes", phases["worker_execution"]["gates"])
        self.assertEqual("serial", phases["integration_review"]["mode"])
        self.assertIn("integration review", phases["integration_review"]["gates"])

    def test_work_producing_routes_get_cycle_contract_but_review_stays_separate(self) -> None:
        for command in sorted(WORK_PRODUCING_COMMANDS):
            with self.subTest(command=command):
                route = resolve_docs(command, None, [], request_classified=True)

                self.assertIn(CYCLE_CONTRACT_GATE, route["gates"])
                self.assertIn("workflows/cycle-contract.md", route["docs"])

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
                self.assertIn("common/source-driven-development.md", route["docs"])
                self.assertIn("workflows/cycle-contract.md", route["docs"])
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
        self.assertIn("workflows/scripted-agent-workflow.md", route["docs"])
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
                    "impact decision: unchanged; reason: no durable behavior, "
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
                fields={"takeaway": "use structured ledger evidence instead of manual finish prose"},
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
                "common/agent-operating-skill.md",
                "workflows/scripted-agent-workflow.md",
            ],
        }

        failures = validate_route_docs_manifest_evidence(
            route,
            {
                ROUTE_DOCS_READ_GATE: (
                    "read routed docs before edits: AGENTS.md and common/agent-operating-skill.md"
                )
            },
            {},
        )

        self.assertTrue(any("route docs read receipt is missing" in failure for failure in failures))

        failures = validate_route_docs_manifest_evidence(
            route,
            {ROUTE_DOCS_READ_GATE: "read all 3 routed docs from the preflight route manifest before edits"},
            {},
        )

        self.assertTrue(any("route docs read receipt is missing" in failure for failure in failures))

        failures = validate_route_docs_manifest_evidence(
            route,
            {ROUTE_DOCS_READ_GATE: "read routed docs before edits with docs-read receipt"},
            {
                "schema_version": 1,
                "route_fingerprint": route_fingerprint(route),
                "doc_count": 3,
                "docs": [
                    {"path": "AGENTS.md", "size_bytes": 1, "sha256": "abc"},
                    {"path": "common/agent-operating-skill.md", "size_bytes": 1, "sha256": "def"},
                    {"path": "workflows/scripted-agent-workflow.md", "size_bytes": 1, "sha256": "ghi"},
                ],
            },
        )

        self.assertEqual([], failures)

    def test_route_docs_read_receipt_must_match_current_preflight_hash(self) -> None:
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
        self.assertIn("workflows/prd-creation.md", prd_route["docs"])
        self.assertIn("workflows/prd-creation.md", product_route["docs"])

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
                self.assertIn("workflows/documentation-update.md", route["docs"])

    def test_docs_route_gets_documentation_enforcement_gates(self) -> None:
        route = resolve_docs("docs", None, [], request_classified=True)

        self.assertIn(SOURCE_DOCS_GATE, route["gates"])
        self.assertIn(DOCUMENTATION_IMPACT_GATE, route["gates"])
        self.assertIn(DOCUMENTATION_GATE, route["gates"])
        self.assertLess(route["gates"].index(SOURCE_DOCS_GATE), route["gates"].index("edit"))
        self.assertLess(route["gates"].index(DOCUMENTATION_IMPACT_GATE), route["gates"].index("edit"))
        self.assertIn("common/source-driven-development.md", route["docs"])

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
        self.assertIn("common/task-intake-effort-routing.md", route["docs"])

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
        triage_doc = (ROOT / "workflows" / "request-triage.md").read_text()

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
        self.assertIn("--boundary-plan-evidence", review_hook["command"])
        self.assertIn("--side-effect-audit-evidence", review_hook["command"])

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
                    "common/agent-operating-skill.md; applied takeaway: wrapper "
                    "receipt policy and gate evidence criteria"
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
                    "selected platform: ios; loaded platforms/ios/ios-architecture.md "
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
                    "evidence: boundary gate and unittest verification command recorded"
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
                    "selected platform: web; loaded platforms/web/web-architecture.md "
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

        self.assertTrue(
            any("cannot use unchanged/not-applicable/no-docs" in failure for failure in failures)
        )

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

    def test_parallel_subagent_evidence_requires_contract_forbidden_scope_and_verification(self) -> None:
        failures = validate_gate_evidence(
            {MULTI_AGENT_GATE: "parallel subagent split with owned scope"},
            [MULTI_AGENT_GATE],
        )

        self.assertTrue(any("owned scope, forbidden scope, contract/brief, and verification" in failure for failure in failures))

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

        self.assertEqual([], failures)

    def test_parallel_subagent_finish_requires_structured_delegation_plan(self) -> None:
        evidence = {
            MULTI_AGENT_GATE: (
                "parallel subagent split: worker docs owns workflows/*.md; "
                "forbidden scope: scripts/*.py; contract brief: report doc gaps; "
                "verification: workflow validate"
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
                "contract_drift_check": "compare worker findings with route gate policy",
                "final_verification": ["python3 -m unittest discover tests"],
            },
        }

        self.assertEqual([], validate_delegation_plan_evidence([MULTI_AGENT_GATE], evidence, plan))

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
                    "evidence: review hook and validation check passed"
                )
            },
            [AGENTIC_RUN_STATE_GATE],
        )

        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
