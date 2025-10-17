"""Shared heuristics for systemic metadata validators."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, Iterable

RISK_TERMS = (
    "risk",
    "hazard",
    "safety",
    "guard",
    "rollback",
    "escalate",
)

MANUAL_RECOVERY_TERMS = (
    "revert",
    "manual",
    "fallback",
    "use current",
    "prior",
    "manual review",
)

REFERENCE_TERMS = (
    "docs/",
    "readme",
    "see ",
    "refer",
    "http",
    "https",
    "capsule",
    "_report",
    "appendix",
)

TOOL_TERMS = (
    "tools/",
    "scripts/",
    "python",
    "bash",
    "teof",
    "cli",
)


def norm_text(text: str) -> str:
    """Normalise whitespace and case for stable heuristics."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def count_patterns(text: str, patterns: Iterable[str]) -> int:
    """Count regex pattern matches within text."""
    return sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in patterns)


def contains_any(text: str, patterns: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


@dataclass(frozen=True)
class SystemicJudgement:
    """Simple structured readiness report."""

    scores: Dict[str, int]
    total: int
    verdict: str
    notes: Dict[str, str]


__all__ = [
    "SystemicJudgement",
    "RISK_TERMS",
    "MANUAL_RECOVERY_TERMS",
    "REFERENCE_TERMS",
    "TOOL_TERMS",
    "norm_text",
    "count_patterns",
    "contains_any",
]
