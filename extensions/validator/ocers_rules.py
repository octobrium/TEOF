"""Shared OCERS heuristics for the minimal validator ensemble."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Dict, Iterable

OCERS_PILLARS = ("O", "C", "E", "R", "S")

# Shared pattern hints reused by validators/evaluators
RISK_TERMS = (
    "risk",
    "hazard",
    "safety",
    "guard",
    "rollback",
)

MANUAL_RECOVERY_TERMS = (
    "revert",
    "manual",
    "fallback",
    "use current",
    "prior",
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
)

TOOL_TERMS = (
    "tools/",
    "scripts/",
    "python",
    "bash",
    "teof",
)


@dataclass(frozen=True)
class OCERSJudgement:
    """Deterministic breakdown of OCERS pillar scores."""

    normalized_text: str
    scores: Dict[str, int]
    total: int
    verdict: str
    notes: Dict[str, str]


def norm_text(text: str) -> str:
    """Normalise whitespace and case for stable heuristics."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def count_patterns(text: str, patterns: Iterable[str]) -> int:
    return sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in patterns)


def contains_any(text: str, patterns: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def score_observation(text: str) -> int:
    observations = count_patterns(text, [r"\bobserv", r"\bmeasure", r"\bdata\b", r"\bevidence\b"])
    humility = count_patterns(text, [r"\buncertain", r"\bassumption", r"\bmight\b", r"\bcould\b", r"\bwe recognize\b"])
    attribution = count_patterns(text, [r"\baccording to\b", r"\bsaid\b", r"\breported\b", r"\bcited\b", r"\banalysts?\b", r"\bpolicymakers?\b"])
    quotes = text.count('"') + text.count('“') + text.count('”')
    score = 1 + min(2, observations) + min(2, humility)
    if attribution > 0:
        score += 1
    if quotes >= 2:
        score += 1
    return max(1, min(5, score))


def score_coherence(text: str) -> int:
    logic = count_patterns(text, [r"\btherefore\b", r"\bthus\b", r"\bhence\b", r"\bconclude", r"\bbecause\b", r"\bpremise\b"])
    contradictions = count_patterns(text, [r"\bcontradict", r"\binconsistent", r"\bparadox"])
    score = 2 + min(2, logic) - min(2, contradictions)
    if count_patterns(text, [r"\bsaid\b", r"\baccording to\b"]) >= 2:
        score = max(score, 3)
    return max(1, min(5, score))


def score_ethics(text: str) -> int:
    pros = count_patterns(text, [r"\btransparen", r"\bethic", r"\bresponsib", r"\baccountab", r"\baudit", r"\bpublic\b", r"\bopen(-|\s)?source"])
    cons = count_patterns(text, [r"\bmanipulat", r"\bexploit", r"\bdeceiv", r"\bobfuscat", r"\bthey don'?t want you to know", r"\bdon'?t trust (government|media)"])
    score = 2 + min(3, pros) - min(2, cons)
    if cons == 0 and count_patterns(text, [r"\bsaid\b", r"\breported\b", r"\baccording to\b"]) > 0:
        score = max(score, 3)
    return max(1, min(5, score))


def score_repro(text: str) -> int:
    methods = count_patterns(text, [r"\bmethod", r"\bprocedure", r"\breplicat", r"\bexperiment", r"\bprotocol", r"\bchecklist"])
    citations = count_patterns(text, [r"\bsource", r"\bcite", r"\breference", r"\bappendix", r"\bdoi\b", r"http(s)?://"])
    numbers = len(re.findall(r"\b\d+(\.\d+)?%?\b", text))
    code_data = count_patterns(text, [r"\bcode\b", r"\breleased?\b", r"\bgithub\b", r"\bdataset"])
    attributions = count_patterns(text, [r"\bsaid\b", r"\baccording to\b", r"\banalysts?\b", r"\bpolicymakers?\b"])
    multi_attrib = attributions >= 2
    score = 1
    if methods > 0:
        score += 2
    if citations > 0:
        score += 2
    if numbers > 1:
        score += 1
    if code_data > 0:
        score += 1
    if multi_attrib:
        score += 1
    if numbers > 0 and attributions > 0:
        score = max(score, 3)
    return max(1, min(5, score))


def score_selfrepair(text: str) -> int:
    repair = count_patterns(text, [
        r"\btest",
        r"\bverify",
        r"\baudit",
        r"\bmonitor",
        r"\bincident reporting",
        r"\bpostmortem",
        r"\bfallback",
        r"\brollback",
        r"\bpause\b",
        r"\boversight",
        r"\bindependent review",
        r"\bred team",
        r"\bupdate",
    ])
    score = 1 + min(4, repair)
    return max(1, min(5, score))


_JUSTIFY_TIPS = {
    "O": "Use evidence/uncertainty or attributed reporting.",
    "C": "Keep claims consistent; connect facts to conclusions.",
    "E": "Avoid manipulative framing; prefer transparency.",
    "R": "Provide sources/figures; multiple attributions help.",
    "S": "Include audits/monitoring/rollback or incident reporting.",
}


def justify(pillar: str, score: int) -> str:
    return f"{pillar}={score}/5 — {_JUSTIFY_TIPS[pillar]}"


def _build_scores(normalized_text: str) -> Dict[str, int]:
    return {
        "O": score_observation(normalized_text),
        "C": score_coherence(normalized_text),
        "E": score_ethics(normalized_text),
        "R": score_repro(normalized_text),
        "S": score_selfrepair(normalized_text),
    }


def evaluate_normalized(normalized_text: str) -> OCERSJudgement:
    scores = _build_scores(normalized_text)
    total = sum(scores.values())
    verdict = "PASS" if total >= 18 and min(scores.values()) >= 3 else "NEEDS WORK"
    notes = {pillar: justify(pillar, scores[pillar]) for pillar in OCERS_PILLARS}
    return OCERSJudgement(
        normalized_text=normalized_text,
        scores=scores,
        total=total,
        verdict=verdict,
        notes=notes,
    )


def evaluate_text(raw_text: str) -> OCERSJudgement:
    normalized = norm_text(raw_text)
    return evaluate_normalized(normalized)


__all__ = [
    "OCERSJudgement",
    "OCERS_PILLARS",
    "RISK_TERMS",
    "MANUAL_RECOVERY_TERMS",
    "REFERENCE_TERMS",
    "TOOL_TERMS",
    "count_patterns",
    "contains_any",
    "evaluate_normalized",
    "evaluate_text",
    "justify",
    "norm_text",
    "score_coherence",
    "score_ethics",
    "score_observation",
    "score_repro",
    "score_selfrepair",
]
