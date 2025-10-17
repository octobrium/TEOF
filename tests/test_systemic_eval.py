from teof.eval.systemic_min import evaluate


def test_structured_queue_item_scores_high():
    text = (
        "# Task: Example anchor guard\n"
        "Goal: Add append-only enforcement for anchors and keep provenance receipts aligned.\n"
        "Systemic Targets: S1 Unity, S4 Defense, S6 Truth\n"
        "Layer Targets: L4 Architecture\n"
        "Coordinate: S4:L4\n"
        "Sunset: Remove if false positives exceed 5% over a 14-day window.\n"
        "Fallback: Manual review in doctor until append-only receipts look healthy.\n"
        "Acceptance: tools/doctor.sh flags failures >= 95% precision; governance/anchors.json prev_content_hash matches SHA-256.\n"
    )
    result = evaluate(text)
    assert result["total"] >= 8
    assert result["scores"]["alignment"] >= 1
    assert result["verdict"] == "ready"


def test_unstructured_text_scores_low():
    text = "Random idea\nWe should try something new without a plan or fallback.\n"
    result = evaluate(text)
    assert result["total"] == 0
    assert all(value == 0 for value in result["scores"].values())
    assert result["verdict"] == "review"
