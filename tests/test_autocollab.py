from scripts.bot.autocollab import infer_risk, infer_acceptance


def make_score(total, verdict="ready", **signals):
    score = {
        "total": total,
        "verdict": verdict,
        "diagnostics": {"signals": signals},
    }
    return score


def test_infer_risk_healthy_profile():
    score = make_score(
        10,
        acceptance_has_paths=True,
        acceptance_has_metrics=True,
        fallback_mentions_manual=True,
        sunset_mentions_trigger=True,
        has_references=True,
    )
    risk = infer_risk(score)
    assert risk["risk_score"] == 0.0
    assert risk["penalties"] == ["healthy"]


def test_infer_risk_penalises_missing_guards():
    score = make_score(
        6,
        acceptance_has_paths=False,
        acceptance_has_metrics=False,
        fallback_mentions_manual=False,
        sunset_mentions_trigger=False,
        has_references=False,
    )
    risk = infer_risk(score)
    assert risk["risk_score"] >= 0.6
    assert "acceptance lacks concrete checks" in risk["penalties"]


def test_infer_acceptance_thresholds():
    passing = make_score(
        9,
        acceptance_has_paths=True,
        fallback_mentions_manual=True,
        sunset_mentions_trigger=True,
    )
    assert infer_acceptance(passing)["accepted"] is True

    failing = make_score(
        8,
        acceptance_has_paths=True,
        fallback_mentions_manual=True,
        sunset_mentions_trigger=True,
    )
    assert infer_acceptance(failing)["accepted"] is False
    failing_signals = make_score(
        9,
        acceptance_has_paths=False,
        fallback_mentions_manual=False,
        sunset_mentions_trigger=False,
    )
    assert infer_acceptance(failing_signals)["accepted"] is False
