from __future__ import annotations

import json
import io
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_finish_common import requires_retrospective
from agent_finish_gate_policy import (
    PLATFORM_SELECTION_GATE,
    PRD_DRAFT_GATE,
    REVIEW_READINESS_GATE,
    VALIDATED_GATES,
    validate_gate_evidence,
)
from agent_finish_check_steps import (
    check_request_intake,
    check_required_gates,
    validate_grill_me_skill_evidence,
)
from agent_gate_evidence import (
    gate_evidence_path_for_preflight,
    merge_gate_evidence_from_ledger,
    record_gate_evidence,
    record_many_gate_evidence,
    reset_gate_evidence_ledger,
    synthesize_gate_evidence,
)
from agent_worker_evidence import worker_reservation_matches
from agent_delegation_plan import validate_delegation_plan_evidence
from agent_global_lessons import (
    lesson_summary,
    retrospective_candidate,
    write_retrospective_candidate,
)
from agent_lesson_store import upsert_retrospective_candidate
from agent_hook_runtime import hook_failure_policy, repair_context_failures
import agent_skill_hooks
from agent_preflight_runtime import (
    AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES as PREFLIGHT_AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES,
    _claude_spill_warnings,
)
from agent_review_hook import review_hook, review_vibeguard_command, workflow_validate_failure_detail
from agent_review_structure import structure_review
from agent_vibeguard_cache import cached_vibeguard
from support.agy_setup import AGY_RUNTIME_BRIDGE_REQUIRED_PHRASES, _agy_runtime_bridge_block
from support.claude_setup import _merge_claude_user_prompt_submit
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
    SKILL_FEEDBACK_HOOK,
    SIDE_EFFECT_AUDIT_GATE,
    SOURCE_DOCS_GATE,
    SOURCE_DOCS_COMMANDS,
    TEST_GATE,
    ALIGNMENT_BRIEF_COMMANDS,
    WORK_PRODUCING_COMMANDS,
)
from workflow_request import infer_concerns_from_request
from workflow_request import classify_request
from workflow_request import classified_route_block_reason
from workflow_request import route_block_reason
from workflow_dispatch import (
    build_dispatch_manifest,
    execute_dispatch_manifest,
    print_dispatch_manifest,
)
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
from workflow_route import resolve_docs, route_hooks
from workflow_search import SearchOutcome, search_docs, search_docs_outcome
from workflow_skill_paths import canonical_doc_path
from workflow_spill import spill_tool_label, validate_spill_label_contracts
from workflow import build_parser, print_dispatch
from workflow_validate import (
    STRICT_CARD_REQUIRED_HEADINGS,
    markdown_files_to_validate,
    removed_cli_option_failures,
)


_PREFLIGHT_SPEC = importlib.util.spec_from_file_location(
    "agent_preflight_under_test", ROOT / "scripts" / "agent-preflight.py"
)
assert _PREFLIGHT_SPEC and _PREFLIGHT_SPEC.loader
agent_preflight = importlib.util.module_from_spec(_PREFLIGHT_SPEC)
_PREFLIGHT_SPEC.loader.exec_module(agent_preflight)

_FINISH_CHECK_SPEC = importlib.util.spec_from_file_location(
    "agent_finish_check_under_test", ROOT / "scripts" / "agent-finish-check.py"
)
assert _FINISH_CHECK_SPEC and _FINISH_CHECK_SPEC.loader
agent_finish_check = importlib.util.module_from_spec(_FINISH_CHECK_SPEC)
_FINISH_CHECK_SPEC.loader.exec_module(agent_finish_check)

_AGENT_HOOK_SPEC = importlib.util.spec_from_file_location(
    "agent_hook_under_test", ROOT / "scripts" / "agent-hook.py"
)
assert _AGENT_HOOK_SPEC and _AGENT_HOOK_SPEC.loader
agent_hook = importlib.util.module_from_spec(_AGENT_HOOK_SPEC)
_AGENT_HOOK_SPEC.loader.exec_module(agent_hook)


def route_doc(path: str) -> str:
    return canonical_doc_path(path)


class ClassificationEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_state_home = os.environ.get("TAO_STATE_HOME")

    def tearDown(self) -> None:
        if self._old_state_home is None:
            os.environ.pop("TAO_STATE_HOME", None)
        else:
            os.environ["TAO_STATE_HOME"] = self._old_state_home

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

    def test_scoped_release_request_routes_without_grill_me(self) -> None:
        classification = classify_request(
            "Deploy Spill macOS app release v2026.28.4 from main HEAD with local "
            "verification, package artifact, tag push, and GitHub Release publication."
        )

        self.assertEqual("clear-scoped", classification["clarity"])
        self.assertEqual("release", classification["recommended_route"])
        self.assertFalse(classification["grill_me"])
        self.assertEqual("work", classification["response_mode"])

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

    def test_clarified_request_with_no_unresolved_behavior_blocker_allows_work(self) -> None:
        self.assertIsNone(
            classified_route_block_reason(
                "feature",
                "user clarified the desired interaction explicitly; "
                "no unresolved behavior blocker remains",
            )
        )

        self.assertIsNotNone(
            classified_route_block_reason(
                "feature",
                "an unresolved behavior blocker remains",
            )
        )

    def test_coordinated_negation_of_blockers_does_not_block_work(self) -> None:
        # A negator does not have to be the token immediately left of the
        # phrase it negates. In a coordinated clause the "no" sits several
        # tokens earlier, and a fixed-width lookbehind could not see it, so
        # evidence stating that nothing is outstanding was read as proof that
        # blockers remain.
        self.assertIsNone(
            classified_route_block_reason(
                "bugfix",
                "scope clarified: no open questions or blockers remain",
            )
        )

        self.assertIsNone(
            classified_route_block_reason(
                "bugfix",
                "scope clarified: no unresolved questions or open blockers",
            )
        )

        # A genuine assertion that work is still outstanding must still block,
        # including when an unrelated earlier clause happens to contain "no".
        for unresolved in (
            "scope clarified: blockers remain",
            "scope clarified: two blockers remain open",
            "scope clarified: no docs changed, blockers remain",
            "scope clarified: no open questions but blockers remain",
        ):
            with self.subTest(unresolved=unresolved):
                self.assertIsNotNone(classified_route_block_reason("bugfix", unresolved))

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

        # Evidence alone is no longer enough. Without a parent capsule there is
        # nothing to exempt and no request to classify, so this must fail loudly
        # rather than sail through an unevaluated route_block_reason(cmd, None).
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

        self.assertEqual(2, supplied.returncode)
        self.assertIn("ready and valid execution capsule", supplied.stderr)
        self.assertIn('--request "<USER_REQUEST>"', supplied.stderr)
        self.assertIn("--advisory", supplied.stderr)

        # The same route with the real request text classifies and proceeds.
        with_request = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "route",
                "review",
                "--project",
                str(ROOT),
                "--request",
                "review the pending changes in scripts/workflow.py",
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

        self.assertEqual(0, with_request.returncode, with_request.stderr)
        route = json.loads(with_request.stdout)
        self.assertTrue(route["request_classified"])
        self.assertEqual("direct question was answered and user asked for review", route["classification_evidence"])

    def test_classified_confirmation_needs_a_capsule_to_skip_reclassifying(self) -> None:
        # A short confirmation is only exempt from reclassification when a
        # parent capsule proves a parent resolved the request; see
        # ClassifiedExemptionCapsuleTests for the capsule-backed true positive.
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "route",
                "review",
                "--project",
                str(ROOT),
                "--request",
                "응",
                "--request-classified",
                "--classification-evidence",
                "answered direct question; separate actionable clear-scoped review",
                "--format",
                "json",
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(2, completed.returncode)
        self.assertIn("needs clarification before route `review`", completed.stderr)

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
                        # The request now always classifies; the evidence check
                        # is what has to reject these, not a skipped classifier.
                        "--request",
                        "update the login screen button in src/login.tsx",
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
                "--request",
                "make it better",
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
                        "--request",
                        "update the login screen button in src/login.tsx",
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


class ClassifiedExemptionCapsuleTests(unittest.TestCase):
    """`--request-classified` is honored only with a valid parent capsule.

    The flag used to be self-asserting: passing it skipped `classify_request`,
    which left `route_block_reason(command, None)` returning immediately. The
    clarify-first/Grill-Me check was not satisfied, it was never evaluated, so
    any caller could open any work route by describing itself as classified.
    """

    # Real user request that opened the session where this defect was found.
    GRILL_ME_REQUEST = "agent를 만들었는데 이게 실제로 잘 동작하는지 검증해줄래?"
    WORKER_ACKNOWLEDGEMENT = "응"
    RESOLVED_EVIDENCE = "answered direct question; separate actionable clear-scoped review"

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.project = root / "project"
        self.rules = root / "rules"
        self._init_repository(self.project, {"app.txt": "app\n"})
        self._init_repository(self.rules, {"guide.md": "# Guide\n"})
        self.route = {
            "command": "review",
            "platform": None,
            "concerns": [],
            "docs": ["guide.md"],
            "required_docs": ["guide.md"],
            "reference_docs": [],
            "gates": ["verify"],
            "missing": [],
            "blocking": [],
        }
        self.evidence_path = self.project / ".tao" / "preflight.json"
        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)
        self.evidence_path.write_text(
            json.dumps(
                {
                    "project": str(self.project.resolve()),
                    "rules": str(self.rules.resolve()),
                    "request_intake": {
                        "request": self.WORKER_ACKNOWLEDGEMENT,
                        "request_classified": True,
                        "classification_evidence": self.RESOLVED_EVIDENCE,
                    },
                    "route": self.route,
                }
            ),
            encoding="utf-8",
        )
        self._write_ledger()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _create_parent_capsule(self) -> None:
        from agent_execution_capsule import refresh_execution_capsule

        capsule = refresh_execution_capsule(
            self.project, self.rules, self.evidence_path, self.route
        )
        self.assertEqual("ready", capsule["phase"])

    def _route(self, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "workflow.py"),
                "route",
                "review",
                "--project",
                str(self.project),
                "--rules",
                str(self.rules),
                "--format",
                "json",
                *extra,
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_valid_parent_capsule_still_skips_reclassifying_a_short_reply(self) -> None:
        # The case the exemption exists for: a worker holds only "응" as request
        # identity, and reclassifying it would falsely reopen Grill-Me after the
        # parent already resolved the request. This must keep working.
        self.assertTrue(classify_request(self.WORKER_ACKNOWLEDGEMENT)["grill_me"])
        self._create_parent_capsule()

        completed = self._route(
            "--request",
            self.WORKER_ACKNOWLEDGEMENT,
            "--request-classified",
            "--classification-evidence",
            self.RESOLVED_EVIDENCE,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["request_classified"])

    def test_without_a_parent_capsule_the_classifier_runs_on_the_request(self) -> None:
        self.assertTrue(classify_request(self.WORKER_ACKNOWLEDGEMENT)["grill_me"])

        completed = self._route(
            "--request",
            self.WORKER_ACKNOWLEDGEMENT,
            "--request-classified",
            "--classification-evidence",
            self.RESOLVED_EVIDENCE,
        )

        self.assertEqual(2, completed.returncode)
        self.assertIn("needs clarification before route `review`", completed.stderr)
        self.assertIn("grill_me: true", completed.stderr)

    def test_real_grill_me_request_cannot_be_waved_through_by_the_flag(self) -> None:
        classification = classify_request(self.GRILL_ME_REQUEST)
        self.assertEqual("vague-action", classification["clarity"])
        self.assertTrue(classification["grill_me"])

        completed = self._route(
            "--request",
            self.GRILL_ME_REQUEST,
            "--request-classified",
            "--classification-evidence",
            "scope clarified: blockers resolved, no blockers remain.",
        )

        self.assertEqual(2, completed.returncode)
        self.assertIn("Grill-Me", completed.stderr)

    def test_classified_without_a_request_or_capsule_is_rejected(self) -> None:
        # The silent hole: route_block_reason(command, None) returned instantly,
        # so this combination bypassed every check while looking like a pass.
        completed = self._route(
            "--request-classified",
            "--classification-evidence",
            "scope clarified: blockers resolved, no blockers remain.",
        )

        self.assertEqual(2, completed.returncode)
        self.assertEqual("", completed.stdout.strip())
        self.assertIn("ready and valid execution capsule", completed.stderr)
        self.assertIn('--request "<USER_REQUEST>"', completed.stderr)
        self.assertIn("--advisory", completed.stderr)

    def test_advisory_route_lists_docs_without_asserting_request_intake(self) -> None:
        completed = self._route("--advisory")

        self.assertEqual(0, completed.returncode, completed.stderr)
        route = json.loads(completed.stdout)
        self.assertTrue(route["advisory"])
        self.assertFalse(route["request_classified"])
        self.assertEqual("", route["classification_evidence"])
        self.assertTrue(
            any("satisfies no downstream gate" in note for note in route["notes"])
        )

    def test_advisory_cannot_be_combined_with_request_classified(self) -> None:
        completed = self._route(
            "--advisory",
            "--request-classified",
            "--classification-evidence",
            "scope clarified: blockers resolved.",
        )

        self.assertEqual(2, completed.returncode)
        self.assertIn("cannot be combined", completed.stderr)

    def _write_ledger(self) -> None:
        from agent_route_state import preflight_evidence_sha256, route_fingerprint

        ledger_path = gate_evidence_path_for_preflight(self.evidence_path)
        ledger_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "created_at": "2026-07-14T00:00:00+00:00",
                    "preflight_evidence": str(self.evidence_path),
                    "preflight_evidence_sha256": preflight_evidence_sha256(self.evidence_path),
                    "route_fingerprint": route_fingerprint(self.route),
                    "entries": [
                        {
                            "created_at": "2026-07-14T00:00:00+00:00",
                            "gate": "request intake",
                            "status": "SUCCESS",
                            "source": "start",
                            "evidence": "preflight request intake completed",
                            "fields": {"classification_evidence": self.RESOLVED_EVIDENCE},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _init_repository(self, path: Path, files: dict) -> None:
        path.mkdir(parents=True)
        (path / ".gitignore").write_text(".tao/\n", encoding="utf-8")
        for relative, content in files.items():
            (path / relative).write_text(content, encoding="utf-8")
        for command in (
            ("init", "-q"),
            ("config", "user.email", "tests@example.invalid"),
            ("config", "user.name", "Tao Agent OS Tests"),
            ("add", "-A"),
            ("commit", "-qm", "initial"),
        ):
            subprocess.run(
                ["git", *command],
                cwd=path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )


if __name__ == "__main__":
    unittest.main()
