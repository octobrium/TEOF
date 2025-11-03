#!/usr/bin/env python3
"""Receipt-backed systemic readiness evaluator."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_ROOT_ENV = "TEOF_RECEIPT_ROOT"
SECTION_KEYS = ("receipts", "evidence", "artifacts", "links")
PATH_TOKEN = re.compile(r"(?:^|[\s,;])((?:_report|capsule|memory|artifacts|docs|queue)/[^\s,;]+)")


@dataclass(frozen=True)
class ReceiptSignals:
    referenced: Sequence[str]
    existing: Sequence[Path]
    hashed: int
    systemic: int
    risk: int
    recovery: int
    verdicts: int


def _resolve_root() -> Path:
    override = os.getenv(RECEIPT_ROOT_ENV)
    if override:
        candidate = Path(override).expanduser()
        if candidate.exists():
            return candidate
    return ROOT


def _parse_sections(text: str) -> Mapping[str, str]:
    try:
        from teof.eval.systemic_min import parse_sections  # type: ignore
    except Exception:  # pragma: no cover - defensive import
        return {}
    return parse_sections(text)


def _candidate_paths(text: str, sections: Mapping[str, str]) -> Iterable[str]:
    seen: set[str] = set()
    for key in SECTION_KEYS:
        raw = sections.get(key)
        if not raw:
            continue
        for part in re.split(r"[\s,;]+", raw):
            candidate = part.strip().strip("`\"'()[]")
            if not candidate:
                continue
            if candidate.startswith((".", "/")) or "/" in candidate:
                seen.add(candidate)
    for match in PATH_TOKEN.findall(text):
        candidate = match.strip().strip("`\"'()[]")
        if candidate:
            seen.add(candidate)
    ordered = sorted(seen)
    for entry in ordered:
        yield entry


def _safe_join(root: Path, token: str) -> Path | None:
    if not token:
        return None
    candidate = Path(token)
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _load_json(path: Path) -> Mapping[str, object] | None:
    if path.suffix not in {".json", ".jsonl"}:
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not text:
        return None
    payload = text.splitlines()[-1] if path.suffix == ".jsonl" else text
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, Mapping) else None


def _count_tokens(data: Mapping[str, object], keys: Sequence[str]) -> int:
    score = 0
    lowered: Dict[str, object] = {key.lower(): value for key, value in data.items()}
    for key in keys:
        if key in lowered:
            score += 1
    return score


def analyse_receipts(text: str, *, root: Path | None = None) -> ReceiptSignals:
    base = root or _resolve_root()
    sections = _parse_sections(text)
    referenced = list(_candidate_paths(text, sections))

    existing: list[Path] = []
    hashed = 0
    systemic = 0
    risk = 0
    recovery = 0
    verdicts = 0

    for token in referenced:
        storage = _safe_join(base, token)
        if not storage or not storage.exists():
            continue
        existing.append(storage)
        data = _load_json(storage)
        if not data:
            continue
        if "receipt_sha256" in data or "hash_sha256" in data:
            hashed += 1
        if "systemic" in data or "systemic_targets" in data:
            systemic += 1
        if any(key in data for key in ("risk", "warnings", "alerts")):
            risk += 1
        if any(key in data for key in ("recovery", "fallback", "rollback", "manual_recovery")):
            recovery += 1
        if any(key in data for key in ("verdict", "status", "state")):
            verdicts += 1

    return ReceiptSignals(
        referenced=referenced,
        existing=existing,
        hashed=hashed,
        systemic=systemic,
        risk=risk,
        recovery=recovery,
        verdicts=verdicts,
    )


def evaluate(text: str, *, root: Path | None = None) -> Dict[str, float]:
    sig = analyse_receipts(text, root=root)
    total_refs = len(sig.referenced)
    existing_refs = len(sig.existing)

    structure = 0.0
    if total_refs:
        structure += 1.0
    if existing_refs >= 2:
        structure += 1.0

    alignment = 0.0
    if sig.systemic:
        alignment += 1.0
    if existing_refs and existing_refs == sig.systemic:
        alignment += 1.0

    verification = 0.0
    if sig.hashed:
        verification += 1.0
    if sig.verdicts:
        verification += 1.0

    risk = 1.0 if sig.risk else 0.0
    recovery = 1.0 if sig.recovery else 0.0

    return {
        "structure": structure,
        "alignment": alignment,
        "verification": verification,
        "risk": risk,
        "recovery": recovery,
    }


__all__ = [
    "ReceiptSignals",
    "analyse_receipts",
    "evaluate",
]
