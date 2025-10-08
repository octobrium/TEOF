"""Generate TEOF-aligned philosophical guidance prompts."""
from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FAQ_PATH = ROOT / "datasets" / "philosophy" / "faq_map.json"


@dataclass(frozen=True)
class FAQEntry:
    """Single FAQ alignment entry."""

    id: str
    keywords: tuple[str, ...]
    question: str
    summary: str
    sources: tuple[str, ...]


def _load_entries(path: Path = DEFAULT_FAQ_PATH) -> List[FAQEntry]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries: List[FAQEntry] = []
    for raw in data:
        entries.append(
            FAQEntry(
                id=str(raw["id"]),
                keywords=tuple(keyword.lower() for keyword in raw.get("keywords", [])),
                question=str(raw["question"]),
                summary=str(raw["summary"]),
                sources=tuple(str(item) for item in raw.get("sources", [])),
            )
        )
    return entries


def _score(question: str, keywords: Sequence[str]) -> int:
    """Naïve keyword hit count."""

    text = question.lower()
    return sum(text.count(keyword) for keyword in keywords)


def select_entry(question: str, *, path: Path = DEFAULT_FAQ_PATH) -> FAQEntry | None:
    """Find the best matching FAQ entry for *question* or ``None`` when no hits."""

    entries = _load_entries(path)
    scored = [(entry, _score(question, entry.keywords)) for entry in entries]
    scored.sort(key=lambda item: item[1], reverse=True)
    if not scored or scored[0][1] == 0:
        return None
    return scored[0][0]


def build_prompt(question: str, *, path: Path = DEFAULT_FAQ_PATH) -> str:
    """Build a guidance prompt grounded in TAP/workflow sources."""

    question_clean = question.strip()
    entry = select_entry(question_clean, path=path)

    base_intro = textwrap.dedent(
        """
        You are assisting with TEOF (The Eternal Observer Framework). Honour Observation → Coherence → Ethics → Reproducibility → Self-repair (OCERS) in every answer.
        Anchor claims in primary documents, require receipts before prescriptive guidance, and disclose limits when evidence is missing.
        """
    ).strip()

    if entry is None:
        guidance = (
            "No specialised mapping exists. Default to TAP (docs/foundation/alignment-protocol/tap.md), "
            "the Commandments (docs/commandments.md), and the Workflow observation rules (docs/workflow.md#observation-primacy)."
        )
        sources_block = "- docs/foundation/alignment-protocol/tap.md\n- docs/commandments.md\n- docs/workflow.md#observation-primacy"
    else:
        guidance = entry.summary
        sources_block = "\n".join(f"- {source}" for source in entry.sources)

    prompt = textwrap.dedent(
        f"""
        {base_intro}

        Question: {question_clean}

        Guidance:
        {guidance}

        Cite these references when responding:
        {sources_block}

        Log receipts for actions under `_report/` so future observers can verify the outcome.
        """
    ).strip()
    return prompt


__all__ = ["build_prompt", "select_entry"]
