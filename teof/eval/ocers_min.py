#!/usr/bin/env python3
"""OCERS v0.2 lightweight scorer for queue/autocollab proposals.

Scores structured queue items on a 0–10 scale (2 points per OCERS pillar)
and emits diagnostics to help downstream agents debug.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable

SECTION_RE = re.compile(r"^[#*\-\s]*([A-Za-z][A-Za-z0-9 /+_-]*)\s*:\s*(.+)$")

@dataclass(frozen=True)
class Signals:
    sections: Dict[str, str]
    has_goal: bool
    goal_substantial: bool
    has_acceptance: bool
    acceptance_has_metrics: bool
    acceptance_has_paths: bool
    acceptance_mentions_tools: bool
    has_ocers_target: bool
    target_mentions_safety: bool
    target_mentions_ethics: bool
    has_sunset: bool
    sunset_mentions_trigger: bool
    has_fallback: bool
    fallback_mentions_manual: bool
    mentions_risk_terms: bool
    has_references: bool
    has_numbers: bool
    section_count: int


EXPECTED_KEYS = {
    "task",
    "goal",
    "ocers_target",
    "sunset",
    "fallback",
    "acceptance",
}


def _normalise_key(raw: str) -> str:
    key = raw.strip().lower()
    key = key.lstrip("#*-").strip()
    key = re.sub(r"\s+", "_", key)
    return key


def parse_sections(text: str) -> Dict[str, str]:
    sections: Dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        match = SECTION_RE.match(line)
        if match:
            key = _normalise_key(match.group(1))
            value = match.group(2).strip()
            sections[key] = value
            current = key
            continue
        stripped = line.strip()
        if not stripped:
            current = None
            continue
        if current and (line.startswith((" ", "\t", "-", "*"))):
            sections[current] = sections.get(current, "") + " " + stripped
        else:
            current = None
    return sections


def _contains(patterns: Iterable[str], text: str) -> bool:
    text_lower = text.lower()
    return any(p in text_lower for p in patterns)


def build_signals(text: str, sections: Dict[str, str]) -> Signals:
    goal = sections.get("goal", "")
    acceptance = sections.get("acceptance", "")
    ocers_target = sections.get("ocers_target", "")
    sunset = sections.get("sunset", "")
    fallback = sections.get("fallback", "")

    acceptance_lower = acceptance.lower()
    fallback_lower = fallback.lower()
    target_lower = ocers_target.lower()
    full_lower = text.lower()

    return Signals(
        sections=sections,
        has_goal=bool(goal.strip()),
        goal_substantial=len(goal.split()) >= 6,
        has_acceptance=bool(acceptance.strip()),
        acceptance_has_metrics=bool(re.search(r"(>=|<=|\\bpass\\b|\\bfail\\b|\\bsha-?256\\b|\\bjson\\b)", acceptance_lower) or re.search(r"\\d", acceptance)),
        acceptance_has_paths=bool(re.search(r"[/\\\\]", acceptance) or re.search(r"\\.(json|py|sh|md|txt|yml|yaml)", acceptance_lower)),
        acceptance_mentions_tools=_contains(("tools/", "scripts/", "python", "bash", "teof"), acceptance_lower),
        has_ocers_target=bool(ocers_target.strip()),
        target_mentions_safety="safety" in target_lower,
        target_mentions_ethics=_contains(("ethic", "cohere", "fair"), target_lower),
        has_sunset=bool(sunset.strip()),
        sunset_mentions_trigger=_contains(("if", "when", "until", "unless", "threshold", ">"), sunset.lower()),
        has_fallback=bool(fallback.strip()),
        fallback_mentions_manual=_contains(("revert", "manual", "fallback", "use current", "prior"), fallback_lower),
        mentions_risk_terms=_contains(("risk", "hazard", "safety", "guard", "rollback"), full_lower),
        has_references=_contains(("docs/", "README", "see ", "refer", "http", "https", "capsule", "_report"), text),
        has_numbers=bool(re.search(r"\\d", text)),
        section_count=len(sections),
    )


def score_observation(sig: Signals) -> int:
    score = 0
    if sig.has_goal:
        score += 1
        if sig.goal_substantial:
            score += 1
    if sig.has_acceptance and (sig.acceptance_has_metrics or sig.acceptance_has_paths or sig.has_references):
        score = max(score, 2)
    return min(score, 2)


def score_coherence(sig: Signals) -> int:
    score = 0
    if sig.has_goal and sig.has_acceptance and sig.has_ocers_target:
        score += 1
    if sig.section_count >= len(EXPECTED_KEYS) or (sig.has_sunset and sig.has_fallback):
        score += 1
    return min(score, 2)


def score_ethics(sig: Signals) -> int:
    score = 0
    if sig.has_sunset and sig.has_fallback:
        score += 1
    if sig.target_mentions_safety or sig.target_mentions_ethics or sig.mentions_risk_terms:
        score += 1
    return min(score, 2)


def score_repro(sig: Signals) -> int:
    score = 0
    if sig.acceptance_mentions_tools or sig.acceptance_has_paths:
        score += 1
    if sig.has_numbers or sig.acceptance_has_metrics or sig.has_references:
        score += 1
    return min(score, 2)


def score_self_repair(sig: Signals) -> int:
    score = 0
    if sig.has_fallback:
        score += 1
    if sig.has_sunset and (sig.sunset_mentions_trigger or sig.fallback_mentions_manual):
        score += 1
    return min(score, 2)


def evaluate(text: str) -> Dict[str, object]:
    sections = parse_sections(text)
    sig = build_signals(text, sections)
    scores = {
        "O": score_observation(sig),
        "C": score_coherence(sig),
        "E": score_ethics(sig),
        "R": score_repro(sig),
        "S": score_self_repair(sig),
    }
    total = int(sum(scores.values()))
    verdict = "review" if total < 7 else "ready"
    diagnostics = {
        "section_count": sig.section_count,
        "has_expected_sections": sorted(EXPECTED_KEYS.intersection(sections)),
        "signals": {
            "goal_substantial": sig.goal_substantial,
            "acceptance_has_metrics": sig.acceptance_has_metrics,
            "acceptance_has_paths": sig.acceptance_has_paths,
            "acceptance_mentions_tools": sig.acceptance_mentions_tools,
            "target_mentions_safety": sig.target_mentions_safety,
            "target_mentions_ethics": sig.target_mentions_ethics,
            "sunset_mentions_trigger": sig.sunset_mentions_trigger,
            "fallback_mentions_manual": sig.fallback_mentions_manual,
            "has_references": sig.has_references,
            "has_numbers": sig.has_numbers,
            "mentions_risk_terms": sig.mentions_risk_terms,
        },
    }
    return {
        "scale": "0-10",
        "scores": scores,
        "total": total,
        "verdict": verdict,
        "diagnostics": diagnostics,
    }


def run(path: Path) -> Dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return evaluate(text)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OCERS v0.2 minimal evaluator")
    parser.add_argument("input", help="Path to queue/proposal markdown")
    parser.add_argument("--compact", action="store_true", help="Emit JSON without indentation")
    args = parser.parse_args(list(argv) if argv is not None else None)

    result = run(Path(args.input))
    if args.compact:
        json.dump(result, sys.stdout, separators=(",", ":"))
        sys.stdout.write("\n")
    else:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via CLI
    raise SystemExit(main())
