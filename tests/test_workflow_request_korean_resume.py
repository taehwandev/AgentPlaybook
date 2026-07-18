from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_request import classified_route_block_reason


class KoreanResumeEvidenceTests(unittest.TestCase):
    def test_accepts_explicit_new_run_approval_for_release(self) -> None:
        evidence = "사용자가 이전 안전 검증 중단 뒤 새 실행으로 계속 진행하도록 명시적으로 승인했다."

        self.assertIsNone(classified_route_block_reason("release", evidence))

    def test_does_not_treat_a_prior_work_question_as_resume_approval(self) -> None:
        evidence = "사용자가 이전 작업에 대해 문의했다."

        self.assertIsNotNone(classified_route_block_reason("release", evidence))

    def test_does_not_treat_negated_resume_as_approval(self) -> None:
        # Regression: the new-run-approval pattern matched the bare trigger
        # word ("재개", "승인", "진행") anywhere within 120 chars of "새
        # 실행"/"별도 작업", with no check for negation. "재개하면 안 된다"
        # (direct negation on the matched trigger) and "재개는 승인되지
        # 않았다" (negation displaced onto a different word, "승인", in a
        # separate clause about the same topic) both explicitly refuse
        # resumption but contained the trigger word, so both were wrongly
        # accepted as approval.
        for evidence in (
            "새 실행을 재개하면 안 된다고 했다.",
            "새 실행을 재개하지 마세요.",
            "새 실행 재개는 승인되지 않았다.",
            "새 실행 진행 불가 통보를 받았다.",
            "새 작업 승인이 없다고 확인됨.",
            "새 실행을 재개할 수 없다고 답변받음.",
            "새 실행은 재개 못 한다.",
        ):
            with self.subTest(evidence=evidence):
                self.assertIsNotNone(classified_route_block_reason("release", evidence))

    def test_accepts_new_run_approval_with_topic_particle(self) -> None:
        evidence = "사용자가 별도 작업으로 명시적으로 진행을 승인했습니다."

        self.assertIsNone(classified_route_block_reason("release", evidence))


if __name__ == "__main__":
    unittest.main()
