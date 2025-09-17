from teof.eval.ocers_min import evaluate


def test_structured_queue_item_scores_high():
    text = (
        "# Task: Example anchor guard\n"
        "Goal: Add append-only enforcement for anchors and keep provenance receipts aligned.\n"
        "OCERS Target: Evidence↑ Safety↑ Coherence↑\n"
        "Sunset: Remove if false positives exceed 5% over a 14-day window.\n"
        "Fallback: Manual review in doctor until append-only receipts look healthy.\n"
        "Acceptance: tools/doctor.sh flags ❌ on mid-file edits; governance/anchors.json prev_content_hash matches SHA-256.\n"
    )
    result = evaluate(text)
    assert result["total"] >= 7
    assert result["scores"]["S"] >= 1
    assert result["verdict"] == "ready"


def test_unstructured_text_scores_low():
    text = "Random idea\nWe should try something new without a plan or fallback.\n"
    result = evaluate(text)
    assert result["total"] == 0
    for value in result["scores"].values():
        assert value == 0
    assert result["verdict"] == "review"
