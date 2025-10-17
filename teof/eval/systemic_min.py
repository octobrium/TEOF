#!/usr/bin/env python3
"""Systemic readiness heuristic for queue/autocollab proposals."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from extensions.validator.systemic_rules import (
    MANUAL_RECOVERY_TERMS,
    REFERENCE_TERMS,
    RISK_TERMS,
    TOOL_TERMS,
    SystemicJudgement,
    contains_any,
)

SECTION_RE = re.compile(r"^[#*\-\s]*([A-Za-z][A-Za-z0-9 /+_-]*)\s*:\s*(.+)$")
SYSTEMIC_TOKEN_RE = re.compile(r"S(10|[1-9])", re.IGNORECASE)
LAYER_TOKEN_RE = re.compile(r"L[0-6]", re.IGNORECASE)

EXPECTED_KEYS = {
    "task",
    "goal",
    "systemic_targets",
    "layer_targets",
    "coordinate",
    "acceptance",
    "sunset",
    "fallback",
}


@dataclass(frozen=True)
class Signals:
    sections: Dict[str, str]
    has_goal: bool
    has_acceptance: bool
    acceptance_has_metrics: bool
    acceptance_mentions_tools: bool
    has_systemic_targets: bool
    systemic_token_count: int
    has_layer_targets: bool
    layer_token_count: int
    has_coordinate: bool
    has_sunset: bool
    sunset_has_trigger: bool
    has_fallback: bool
    fallback_mentions_manual: bool
    mentions_risk_terms: bool
    has_references: bool
    has_numbers: bool
    section_count: int


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


def build_signals(text: str, sections: Dict[str, str]) -> Signals:
    goal = sections.get("goal", "")
    acceptance = sections.get("acceptance", "")
    systemic_raw = sections.get("systemic_targets", "")
    layer_raw = sections.get("layer_targets", "")
    coordinate = sections.get("coordinate", "")
    sunset = sections.get("sunset", "")
    fallback = sections.get("fallback", "")

    acceptance_lower = acceptance.lower()
    fallback_lower = fallback.lower()
    sunset_lower = sunset.lower()

    systemic_tokens = set(token.upper() for token in SYSTEMIC_TOKEN_RE.findall(systemic_raw))
    layer_tokens = set(token.upper() for token in LAYER_TOKEN_RE.findall(layer_raw))
    if not layer_tokens and coordinate:
        layer_tokens.update(token.upper() for token in LAYER_TOKEN_RE.findall(coordinate))
    if not systemic_tokens and coordinate:
        systemic_tokens.update(token.upper() for token in SYSTEMIC_TOKEN_RE.findall(coordinate))

    has_numbers = bool(re.search(r"\d", text))

    return Signals(
        sections=sections,
        has_goal=bool(goal.strip()),
        has_acceptance=bool(acceptance.strip()),
        acceptance_has_metrics=bool(
            re.search(r"(>=|<=|\bpass\b|\bfail\b|\bsha-?256\b|\bjson\b|\d%%?)", acceptance_lower)
        ),
        acceptance_mentions_tools=contains_any(acceptance, TOOL_TERMS),
        has_systemic_targets=bool(systemic_tokens),
        systemic_token_count=len(systemic_tokens),
        has_layer_targets=bool(layer_tokens),
        layer_token_count=len(layer_tokens),
        has_coordinate=bool(coordinate.strip()),
        has_sunset=bool(sunset.strip()),
        sunset_has_trigger=contains_any(sunset_lower, ("if", "when", "until", "unless", "threshold", ">")),
        has_fallback=bool(fallback.strip()),
        fallback_mentions_manual=contains_any(fallback_lower, MANUAL_RECOVERY_TERMS),
        mentions_risk_terms=contains_any(text, RISK_TERMS),
        has_references=contains_any(text, REFERENCE_TERMS),
        has_numbers=has_numbers,
        section_count=len(sections),
    )


def score_structure(sig: Signals) -> int:
    score = 0
    if sig.has_goal and sig.has_acceptance:
        score += 1
    if sig.section_count >= len(EXPECTED_KEYS) or sig.has_coordinate:
        score += 1
    return score


def score_alignment(sig: Signals) -> int:
    score = 0
    if sig.has_systemic_targets:
        score += 1
    if sig.has_layer_targets:
        score += 1
    return score


def score_verification(sig: Signals) -> int:
    score = 0
    if sig.acceptance_has_metrics or sig.has_numbers:
        score += 1
    if sig.has_references or sig.acceptance_mentions_tools:
        score += 1
    return score


def score_risk(sig: Signals) -> int:
    score = 0
    if sig.mentions_risk_terms or sig.sunset_has_trigger:
        score += 1
    if sig.has_sunset:
        score += 1
    return score


def score_recovery(sig: Signals) -> int:
    score = 0
    if sig.has_fallback:
        score += 1
    if sig.fallback_mentions_manual:
        score += 1
    return score


def _build_scores(sig: Signals) -> Dict[str, int]:
    return {
        "structure": score_structure(sig),
        "alignment": score_alignment(sig),
        "verification": score_verification(sig),
        "risk": score_risk(sig),
        "recovery": score_recovery(sig),
    }


def evaluate(text: str) -> Dict[str, object]:
    sections = parse_sections(text)
    sig = build_signals(text, sections)
    scores = _build_scores(sig)
    total = sum(scores.values())
    verdict = "ready" if total >= 8 and all(value >= 1 for value in scores.values()) else "review"
    judgement = SystemicJudgement(
        scores=scores,
        total=total,
        verdict=verdict,
        notes={
            "structure": "Ensure goal, acceptance, and key sections are present.",
            "alignment": "Provide systemic and layer targets aligned with coordinates.",
            "verification": "Acceptance should include metrics, references, or tooling.",
            "risk": "Document risk triggers and sunsets.",
            "recovery": "Include clear fallback and manual recovery steps.",
        },
    )
    return {
        "scores": judgement.scores,
        "total": judgement.total,
        "verdict": judgement.verdict,
        "signals": {
            "has_goal": sig.has_goal,
            "has_acceptance": sig.has_acceptance,
            "acceptance_has_metrics": sig.acceptance_has_metrics,
            "acceptance_mentions_tools": sig.acceptance_mentions_tools,
            "has_systemic_targets": sig.has_systemic_targets,
            "systemic_token_count": sig.systemic_token_count,
            "has_layer_targets": sig.has_layer_targets,
            "layer_token_count": sig.layer_token_count,
            "has_coordinate": sig.has_coordinate,
            "has_sunset": sig.has_sunset,
            "sunset_has_trigger": sig.sunset_has_trigger,
            "has_fallback": sig.has_fallback,
            "fallback_mentions_manual": sig.fallback_mentions_manual,
            "mentions_risk_terms": sig.mentions_risk_terms,
            "has_references": sig.has_references,
            "has_numbers": sig.has_numbers,
            "section_count": sig.section_count,
        },
        "sections": sorted(sections.keys()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to input .txt document")
    parser.add_argument("outdir", type=Path, help="Directory for JSON output")
    args = parser.parse_args(argv)

    raw = args.input.read_text(encoding="utf-8", errors="ignore")
    result = evaluate(raw)

    args.outdir.mkdir(parents=True, exist_ok=True)
    payload = {
        "stamp": Path(args.input).stat().st_mtime,
        "input_file": args.input.name,
        "scores": result["scores"],
        "total": result["total"],
        "verdict": result["verdict"],
        "signals": result["signals"],
    }
    output_path = args.outdir / f"{args.input.stem}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[systemic] {args.input.stem}: total={result['total']}/10 verdict={result['verdict']} {result['scores']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
