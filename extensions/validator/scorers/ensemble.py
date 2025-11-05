#!/usr/bin/env python3
"""Minimal systemic readiness ensemble scorer with typed runners and safety checks."""
from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Callable, Dict, Mapping, MutableMapping, Sequence

from teof.eval import systemic_receipts

_PILLARS: tuple[str, ...] = ("structure", "alignment", "verification", "risk", "recovery")
RunnerResult = Dict[str, float]
Runner = Callable[[str], RunnerResult]
_RUNNER_TAG_RE = re.compile(r"^[A-Z0-9]{1,8}$")


def load_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def _ensure_scores(payload: Mapping[str, float], *, name: str) -> RunnerResult:
    result: RunnerResult = {pillar: float(payload[pillar]) for pillar in _PILLARS}
    result["name"] = name  # type: ignore[assignment]
    return result


def run_heuristic(text: str) -> RunnerResult:
    mod = importlib.import_module("extensions.validator.teof_systemic_min")
    result = mod.evaluate_cli(text)
    scores = result.get("scores", {})
    payload = {pillar: float(scores.get(pillar, 0)) for pillar in _PILLARS}
    return _ensure_scores(payload, name="H")


def run_receipts(text: str) -> RunnerResult:
    scores = systemic_receipts.evaluate(text)
    payload = {pillar: float(scores.get(pillar, 0.0)) for pillar in _PILLARS}
    return _ensure_scores(payload, name="R")


_RUNNERS: Dict[str, Runner] = {"H": run_heuristic, "R": run_receipts}


def register_runner(tag: str, runner: Runner, *, overwrite: bool = False) -> None:
    if not isinstance(tag, str) or not _RUNNER_TAG_RE.fullmatch(tag):
        raise ValueError("runner tag must be 1–8 uppercase alphanumeric characters")
    if not callable(runner):
        raise TypeError("runner must be callable")
    if not overwrite and tag in _RUNNERS:
        raise ValueError(f"runner '{tag}' already registered; pass overwrite=True to replace it")
    _RUNNERS[tag] = runner


def available_runners() -> Sequence[str]:
    return tuple(sorted(_RUNNERS))


def _resolve_runner(tag: str) -> Runner:
    try:
        return _RUNNERS[tag]
    except KeyError as exc:  # pragma: no cover - defensive path
        available = ", ".join(sorted(_RUNNERS)) or "<none>"
        raise KeyError(f"unknown runner '{tag}'. Available runners: {available}") from exc


def ensemble(scores: Sequence[RunnerResult], weights: Mapping[str, float] | None = None) -> Dict[str, float]:
    if not scores:
        return {pillar: 0.0 for pillar in (*_PILLARS, "total")}

    weight_map: MutableMapping[str, float] = {name: float(value) for name, value in (weights or {}).items()}
    totals: Dict[str, float] = {pillar: 0.0 for pillar in _PILLARS}
    weight_sums: Dict[str, float] = {name: 0.0 for name in _RUNNERS}

    for score in scores:
        name = str(score.get("name"))
        weight = weight_map.get(name, 1.0)
        weight_sums[name] = weight_sums.get(name, 0.0) + weight
        for pillar in _PILLARS:
            totals[pillar] += float(score[pillar]) * weight

    averaged: Dict[str, float] = {}
    for pillar in _PILLARS:
        denominator = sum(weight_sums.values()) or 1.0
        averaged[pillar] = round(totals[pillar] / denominator, 2)
    averaged["total"] = round(sum(averaged[pillar] for pillar in _PILLARS), 2)
    return averaged


def score_file(inp: str | Path, which: Sequence[str] = ("H", "R"), weights: Mapping[str, float] | None = None) -> Dict[str, object]:
    text = load_text(inp)
    parts: list[RunnerResult] = []
    for tag in which:
        try:
            runner = _resolve_runner(tag)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        result = dict(runner(text))
        result.setdefault("name", tag)
        parts.append(result)
    agg = ensemble(parts, weights)
    return {"by_scorer": parts, "ensemble": agg}


__all__ = [
    "available_runners",
    "ensemble",
    "load_text",
    "register_runner",
    "run_heuristic",
    "score_file",
]
