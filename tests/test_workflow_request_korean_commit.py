from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_request import classified_route_block_reason


class KoreanCommitEvidenceTests(unittest.TestCase):
    def test_accepts_commit_with_attached_korean_verb_ending(self) -> None:
        evidence = "사용자가 모든 변경을 분리해서 커밋하라고 명시함"

        self.assertIsNone(classified_route_block_reason("git_commit", evidence))

    def test_does_not_treat_uncommitted_as_commit_action(self) -> None:
        evidence = "미커밋 변경을 검토하는 범위가 명확함"

        self.assertIsNotNone(classified_route_block_reason("git_commit", evidence))

    def test_does_not_treat_comparison_as_commit_action(self) -> None:
        # Regression: "커밋보다" ("rather than a commit") is a comparison, not
        # a request or approval to commit; the old regex matched the bare
        # "커밋" substring regardless of what followed it.
        evidence = "커밋보다 더 중요한 작업을 먼저 처리해야 함"

        self.assertIsNotNone(classified_route_block_reason("git_commit", evidence))

    def test_does_not_treat_explicit_negation_as_commit_action(self) -> None:
        # Regression: "커밋하지 마" ("don't commit") must not be read as
        # approval to run the commit route.
        for evidence in ("절대 커밋하지 마", "커밋하지 마세요", "커밋하지 않을 것"):
            with self.subTest(evidence=evidence):
                self.assertIsNotNone(classified_route_block_reason("git_commit", evidence))

    def test_accepts_commit_with_please_ending(self) -> None:
        evidence = "변경 사항을 커밋해줘"

        self.assertIsNone(classified_route_block_reason("git_commit", evidence))

    def test_does_not_treat_particle_attached_negation_as_commit_action(self) -> None:
        # Regression: the first negation fix only guarded the no-particle
        # form ("커밋하지 마"); the equally common object-particle form
        # ("커밋을 하지 마세요") still matched as a positive commit action.
        for evidence in ("커밋을 하지 마세요", "커밋을 하면 안 돼요", "커밋를 하지 마"):
            with self.subTest(evidence=evidence):
                self.assertIsNotNone(classified_route_block_reason("git_commit", evidence))

    def test_does_not_treat_topic_particle_or_adverb_negation_as_commit_action(self) -> None:
        # Regression: the topic particle form ("커밋은 하지 마") and the
        # adverb-negation form ("커밋 안 해", no "-지 마" suffix at all)
        # still matched as a positive commit action.
        for evidence in ("커밋은 하지 마", "커밋 안 해", "커밋은 안 해"):
            with self.subTest(evidence=evidence):
                self.assertIsNotNone(classified_route_block_reason("git_commit", evidence))

    def test_does_not_treat_metalinguistic_reference_as_commit_action(self) -> None:
        # Regression: "커밋이라고 부른다" ("it's called a commit") refers to
        # the word, not a request to perform one.
        evidence = "커밋이라고 부른다"

        self.assertIsNotNone(classified_route_block_reason("git_commit", evidence))

    def test_does_not_treat_passive_negation_as_commit_action(self) -> None:
        # Regression: the negation deny-list only covered 하다 conjugations
        # ("안 해", "하지 마"). The passive 되다 family ("안 됐다", "되지
        # 않았다") describes that a commit was NOT made, but slipped through
        # as a plain positive commit mention because "됐"/"되지" never
        # matched the 하다-only alternatives.
        for evidence in (
            "커밋되지 않았어요",
            "아직 커밋 안 됐어요",
            "커밋이 안됐습니다",
            "커밋이 안 되면 안 돼요",
        ):
            with self.subTest(evidence=evidence):
                self.assertIsNotNone(classified_route_block_reason("git_commit", evidence))


if __name__ == "__main__":
    unittest.main()
