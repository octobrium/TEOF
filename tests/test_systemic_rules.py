from extensions.validator.systemic_rules import (
    MANUAL_RECOVERY_TERMS,
    RISK_TERMS,
    contains_any,
    norm_text,
)
from teof.eval.systemic_min import evaluate


def test_norm_text_collapses_whitespace_and_case():
    assert norm_text("  Héllo   WORLD\n") == "héllo world"


def test_contains_any_is_case_insensitive():
    assert contains_any("Fallback procedures in place", MANUAL_RECOVERY_TERMS)
    assert contains_any("Guard rails help", RISK_TERMS)
    assert not contains_any("plain statement", ("risk",))


def test_evaluate_text_produces_expected_scores():
    sample = (
        "# Task: Validate systemic readiness\n"
        "Goal: Ensure queue metadata includes coordinates and recovery paths.\n"
        "Systemic Targets: S1 Unity, S4 Resilience\n"
        "Layer Targets: L5 Workflow\n"
        "Coordinate: S4:L5\n"
        "Acceptance: run tools/check.sh >= 90% pass rate; publish receipts to docs/status.md.\n"
        "Sunset: Retire once systemic targets shift or incidents exceed 1 per week.\n"
        "Fallback: Manual review with rollback playbook; revert to previous policy if guard fails.\n"
    )
    result = evaluate(sample)
    assert result["total"] >= 8
    assert result["verdict"] == "ready"
    assert result["scores"]["alignment"] >= 1
