from __future__ import annotations

import json
import inspect
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import agent_global_lessons
import agent_lesson_store
import agent_skill_learning
import agent_skill_maintenance
from agent_review_hook import review_outcome_failures
from agent_skill_learning import (
    curate_observations,
    record_observation,
    review_candidate,
)
from agent_skill_maintenance import complete_verified_skill_maintenance


class AgentSkillLearningTests(unittest.TestCase):
    def test_legacy_single_hop_exports_are_removed(self) -> None:
        self.assertFalse(hasattr(agent_global_lessons, "process_skill_feedback"))
        self.assertFalse(hasattr(agent_global_lessons, "skill_feedback_candidate"))
        self.assertFalse(hasattr(agent_lesson_store, "upsert_candidate"))
        self.assertFalse(hasattr(agent_lesson_store, "promote_candidate"))
        self.assertFalse(hasattr(agent_skill_learning, "complete_maintenance"))
        self.assertFalse(hasattr(agent_skill_maintenance, "_record_verified_application"))
        self.assertEqual(
            ["complete_verified_skill_maintenance"],
            agent_skill_maintenance.__all__,
        )
        parameters = inspect.signature(
            agent_skill_maintenance.complete_verified_skill_maintenance
        ).parameters
        self.assertNotIn("runner", parameters)
        self.assertNotIn("verification_receipt", parameters)

    def test_observation_replay_is_idempotent_and_content_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            first = record_observation(
                root,
                occurrence_id="private-runtime-run-one",
                skill_id="verification_policy",
                signal="missing_structured_evidence",
            )
            replay = record_observation(
                root,
                occurrence_id="private-runtime-run-one",
                skill_id="verification_policy",
                signal="missing_structured_evidence",
            )
            distinct = record_observation(
                root,
                occurrence_id="private-runtime-run-two",
                skill_id="verification_policy",
                signal="missing_structured_evidence",
            )

            self.assertTrue(first["created"])
            self.assertFalse(first["idempotent"])
            self.assertFalse(replay["created"])
            self.assertTrue(replay["idempotent"])
            self.assertEqual(first["observation_id"], replay["observation_id"])
            self.assertTrue(distinct["created"])
            self.assertNotEqual(first["observation_id"], distinct["observation_id"])

            persisted = "\n".join(
                path.read_text(encoding="utf-8") for path in root.rglob("*.json")
            )
            self.assertNotIn("private-runtime-run-one", persisted)
            self.assertNotIn("private-runtime-run-two", persisted)

    def test_curator_queues_review_only_after_two_distinct_occurrences(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record_observation(
                root,
                occurrence_id="run-one",
                skill_id="verification_policy",
                signal="missing_structured_evidence",
            )

            first = curate_observations(root, min_occurrences=2)
            self.assertEqual([], first["queued"])
            self.assertEqual(0, first["ready_count"])

            # A replay of the same run is not a second occurrence.
            record_observation(
                root,
                occurrence_id="run-one",
                skill_id="verification_policy",
                signal="missing_structured_evidence",
            )
            replay = curate_observations(root, min_occurrences=2)
            self.assertEqual([], replay["queued"])
            self.assertEqual(0, replay["ready_count"])

            record_observation(
                root,
                occurrence_id="run-two",
                skill_id="verification_policy",
                signal="missing_structured_evidence",
            )
            ready = curate_observations(root, min_occurrences=2)

            self.assertEqual(1, len(ready["queued"]))
            self.assertEqual(1, ready["ready_count"])
            self.assertGreaterEqual(ready["scanned"], 1)

            repeated_curation = curate_observations(root, min_occurrences=2)
            self.assertEqual([], repeated_curation["queued"])
            self.assertEqual(0, repeated_curation["ready_count"])

    def test_no_change_review_closes_candidate_without_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            candidate_id = self._ready_candidate(root, signal="already_covered")

            reviewed = review_candidate(root, candidate_id, decision="no_change")

            self.assertTrue(reviewed["updated"])
            self.assertEqual(candidate_id, reviewed["candidate_id"])
            self.assertEqual("no_change", reviewed["status"])
            refused = complete_verified_skill_maintenance(
                root,
                project=root,
                rules=root,
                candidate_id=candidate_id,
                outcome="applied",
                verification_kind="unittest",
                target="missing/SKILL.md",
                test_selector="tests.test_agent_skill_learning",
            )
            self.assertFalse(refused["updated"])
            self.assertEqual("candidate_not_staged", refused["reason"])

    def test_stage_patch_is_staged_only_and_completion_requires_staged_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            canonical_skill = (
                root / "common" / "skills" / "verification-policy" / "SKILL.md"
            )
            canonical_skill.parent.mkdir(parents=True)
            canonical_skill.write_text("canonical skill sentinel\n", encoding="utf-8")
            candidate_id = self._ready_candidate(root, signal="missing_checklist_step")

            staged = review_candidate(
                root,
                candidate_id,
                decision="stage_patch",
                gap_type="missing_verification_rule",
                change_type="guidance_patch",
                promotion_target="verification_policy",
            )

            self.assertTrue(staged["updated"])
            self.assertEqual(candidate_id, staged["candidate_id"])
            self.assertEqual("staged_patch", staged["status"])
            self.assertEqual("canonical skill sentinel\n", canonical_skill.read_text())

            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", canonical_skill.relative_to(root)], cwd=root, check=True)
            with patch(
                "agent_skill_maintenance.run_verification_command",
                return_value={"returncode": 1},
            ):
                failed_verification = complete_verified_skill_maintenance(
                    root,
                    project=root,
                    rules=root,
                    candidate_id=candidate_id,
                    outcome="applied",
                    verification_kind="unittest",
                    target=str(canonical_skill.relative_to(root)),
                    test_selector="tests.test_skill_maintenance",
                )
            self.assertFalse(failed_verification["updated"])
            self.assertEqual("maintenance_verification_failed", failed_verification["reason"])
            def change_target_during_verification(_command: list[str], _cwd: Path):
                canonical_skill.write_text("changed during verification\n", encoding="utf-8")
                return {"returncode": 0}

            with patch(
                "agent_skill_maintenance.run_verification_command",
                side_effect=change_target_during_verification,
            ):
                raced = complete_verified_skill_maintenance(
                    root,
                    project=root,
                    rules=root,
                    candidate_id=candidate_id,
                    outcome="applied",
                    verification_kind="unittest",
                    target=str(canonical_skill.relative_to(root)),
                    test_selector="tests.test_skill_maintenance",
                )
            self.assertFalse(raced["updated"])
            self.assertEqual(
                "maintenance_target_changed_during_verification",
                raced["reason"],
            )
            canonical_skill.write_text("canonical skill sentinel\n", encoding="utf-8")
            (root / "test_skill_maintenance.py").write_text(
                "import unittest\n\n"
                "class LiveVerificationTest(unittest.TestCase):\n"
                "    def test_live_command(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            completed = complete_verified_skill_maintenance(
                root,
                project=root,
                rules=root,
                candidate_id=candidate_id,
                outcome="applied",
                verification_kind="unittest",
                target=str(canonical_skill.relative_to(root)),
                test_selector="test_skill_maintenance",
            )
            self.assertTrue(completed["updated"])
            self.assertEqual(candidate_id, completed["candidate_id"])
            self.assertEqual("applied", completed["status"])
            self.assertEqual("unittest", completed["verification_kind"])
            self.assertEqual("canonical skill sentinel\n", canonical_skill.read_text())

            rejected_id = self._ready_candidate(root, signal="unsafe_default_patch")
            review_candidate(
                root,
                rejected_id,
                decision="stage_patch",
                gap_type="unsafe_default",
                change_type="guidance_patch",
                promotion_target="verification_policy",
            )
            rejected = complete_verified_skill_maintenance(
                root,
                project=root,
                rules=root,
                candidate_id=rejected_id,
                outcome="rejected",
            )
            self.assertTrue(rejected["updated"])
            self.assertEqual("rejected", rejected["status"])
            self.assertEqual("canonical skill sentinel\n", canonical_skill.read_text())

    def test_unsafe_slugs_are_rejected_without_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for skill_id, signal in (
                ("../verification_policy", "missing_evidence"),
                ("verification_policy", "contains private prose"),
                ("VerificationPolicy", "missing_evidence"),
            ):
                with self.subTest(skill_id=skill_id, signal=signal):
                    rejected = record_observation(
                        root,
                        occurrence_id="run-one",
                        skill_id=skill_id,
                        signal=signal,
                    )
                    self.assertFalse(rejected["created"])
                    self.assertEqual("unsafe_observation_fields", rejected["reason"])

            self.assertEqual([], list(root.rglob("*.json")))

    def test_unsafe_review_fields_and_missing_candidates_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            candidate_id = self._ready_candidate(root, signal="missing_review_rule")

            unsafe = review_candidate(
                root,
                candidate_id,
                decision="stage_patch",
                gap_type="../private-gap",
                change_type="guidance_patch",
                promotion_target="verification_policy",
            )
            self.assertFalse(unsafe["updated"])
            self.assertEqual("unsafe_review_fields", unsafe["reason"])

            missing_review = review_candidate(
                root,
                "0" * 16,
                decision="no_change",
            )
            self.assertFalse(missing_review["updated"])
            self.assertEqual("candidate_not_found", missing_review["reason"])

            missing_completion = complete_verified_skill_maintenance(
                root,
                project=root,
                rules=root,
                candidate_id="0" * 16,
                outcome="applied",
                verification_kind="unittest",
                target="missing/SKILL.md",
                test_selector="tests.test_agent_skill_learning",
            )
            self.assertFalse(missing_completion["updated"])
            self.assertEqual("candidate_not_found", missing_completion["reason"])

    def test_curator_rejects_tampered_candidate_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for occurrence_id in ("run-one", "run-two"):
                record_observation(
                    root,
                    occurrence_id=occurrence_id,
                    skill_id="verification_policy",
                    signal="missing_review_rule",
                )
            for path in (root / "skill-learning" / "observations").glob("*.json"):
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["candidate_id"] = "0" * 16
                path.write_text(json.dumps(payload), encoding="utf-8")

            curated = curate_observations(root)

            self.assertEqual([], curated["queued"])
            self.assertEqual(0, curated["ready_count"])

    def test_review_outcome_findings_are_blocking(self) -> None:
        self.assertEqual([], review_outcome_failures("pass"))
        self.assertTrue(review_outcome_failures("findings"))

    def _ready_candidate(self, root: Path, *, signal: str) -> str:
        for occurrence_id in ("run-one", "run-two"):
            record_observation(
                root,
                occurrence_id=occurrence_id,
                skill_id="verification_policy",
                signal=signal,
            )
        result = curate_observations(root, min_occurrences=2)
        self.assertEqual(1, result["ready_count"])
        return str(result["queued"][0])


if __name__ == "__main__":
    unittest.main()
