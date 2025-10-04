from __future__ import annotations

from extensions.prompts import philosophy


def test_match_known_question() -> None:
    question = "What is the meaning of life?"
    prompt = philosophy.build_prompt(question)
    assert "Observation → Coherence" in prompt
    assert "docs/foundation/alignment-protocol/tap.md#meaning" in prompt
    assert "docs/whitepaper.md#purpose" in prompt


def test_unknown_question_defaults() -> None:
    question = "Describe TEOF posture on astrophysics"
    entry = philosophy.select_entry(question)
    assert entry is None
    prompt = philosophy.build_prompt(question)
    assert "docs/commandments.md" in prompt
    assert "Receipts" in prompt or "receipts" in prompt
