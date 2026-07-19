"""Finish evidence validation for lightweight retrospective learning."""

from __future__ import annotations

import re


RETROSPECTIVE_OUTCOMES = {
    "no_reusable_gap",
    "reusable_gap",
    "no_skill_used",
}
RETROSPECTIVE_OBSERVATION_STATES = {
    "not_needed",
    "recorded",
    "deferred",
}


def validate_retrospective_check(evidence: str) -> list[str]:
    """Require an explicit skill check while keeping follow-up non-blocking."""

    text = evidence.strip()
    if not text:
        return ["retrospective check evidence is required"]

    skills_checked = _field(text, "skills checked")
    outcome = _field(text, "outcome").lower()
    observation = _field(text, "observation").lower()
    missing = [
        label
        for label, value in (
            ("skills checked", skills_checked),
            ("outcome", outcome),
            ("observation", observation),
        )
        if not value
    ]
    if missing:
        return [
            "retrospective check evidence must state " + ", ".join(missing)
        ]

    failures: list[str] = []
    if outcome not in RETROSPECTIVE_OUTCOMES:
        failures.append(
            "retrospective check outcome must be no_reusable_gap, "
            "reusable_gap, or no_skill_used"
        )
    if observation not in RETROSPECTIVE_OBSERVATION_STATES:
        failures.append(
            "retrospective check observation must be not_needed, recorded, or deferred"
        )
    if failures:
        return failures

    if outcome == "reusable_gap" and observation not in {"recorded", "deferred"}:
        failures.append(
            "retrospective check with reusable_gap must record or defer one skill observation"
        )
    if outcome in {"no_reusable_gap", "no_skill_used"} and observation != "not_needed":
        failures.append(
            f"retrospective check with {outcome} must use observation: not_needed"
        )
    if outcome == "no_skill_used" and skills_checked.lower() not in {
        "none",
        "none_loaded",
        "no_skill_used",
    }:
        failures.append(
            "retrospective check with no_skill_used must set skills checked to none"
        )
    if outcome != "no_skill_used" and skills_checked.lower() in {
        "none",
        "none_loaded",
        "no_skill_used",
    }:
        failures.append(
            "retrospective check must name the skill or skills evaluated"
        )
    return failures


def _field(evidence: str, label: str) -> str:
    match = re.search(
        rf"(?:^|[;\n])\s*{re.escape(label)}\s*[:=]\s*([^;\n]+)",
        evidence,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""
