from extensions.validator.ocers_rules import (
    MANUAL_RECOVERY_TERMS,
    RISK_TERMS,
    contains_any,
    evaluate_text,
    norm_text,
)


def test_norm_text_collapses_whitespace_and_case():
    assert norm_text("  Héllo   WORLD\n") == "héllo world"


def test_contains_any_is_case_insensitive():
    assert contains_any("Fallback procedures in place", MANUAL_RECOVERY_TERMS)
    assert contains_any("Guard rails help", RISK_TERMS)
    assert not contains_any("plain statement", ("risk",))


def test_evaluate_text_produces_expected_scores():
    sample = (
        "According to researchers, the team conducted audits and published code. "
        "We will monitor updates and revert if needed."
    )
    judgement = evaluate_text(sample)
    assert judgement.total == 13
    assert judgement.scores["O"] == 2
    assert judgement.scores["S"] >= 4
