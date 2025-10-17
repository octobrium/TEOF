"""Helpers for working with systemic axis metadata."""
from __future__ import annotations

import re
from typing import Iterable, List

AXIS_RANGE = range(1, 11)
AXIS_TOKENS = tuple(f"S{idx}" for idx in AXIS_RANGE)
AXIS_ORDER_INDEX = {token: pos for pos, token in enumerate(AXIS_TOKENS)}

LEGACY_LOOP_AXIS_MAP = {
    "observation": ("S1", "S2"),
    "coherence": ("S3", "S6"),
    "ethics": ("S4", "S6", "S8"),
    "reproducibility": ("S5", "S6"),
    "self-repair": ("S4", "S10"),
    "self repair": ("S4", "S10"),
    "clarity": ("S6",),
    "evidence": ("S5", "S6"),
    "safety": ("S4", "S8"),
    "outreach": ("S3", "S7"),
    "impact": ("S7",),
    "throughput": ("S2", "S5"),
}

AXIS_PATTERN = re.compile(r"S\s*([0-9]{1,2})", re.IGNORECASE)


def _dedupe_preserve(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def normalize_axis(token: str | None) -> str | None:
    if not token:
        return None
    cleaned = token.strip().upper()
    if not cleaned:
        return None
    if cleaned.startswith("S"):
        cleaned = cleaned[1:]
    digits = "".join(ch for ch in cleaned if ch.isdigit())
    if not digits:
        return None
    try:
        value = int(digits)
    except ValueError:
        return None
    if value not in AXIS_RANGE:
        return None
    return f"S{value}"


def sort_axes(axes: Iterable[str]) -> List[str]:
    tokens = [axis for axis in axes if axis in AXIS_ORDER_INDEX]
    unique = _dedupe_preserve(tokens)
    return sorted(unique, key=lambda entry: AXIS_ORDER_INDEX[entry])


def parse_axis_tokens(text: str | None) -> List[str]:
    if not text:
        return []
    matches = [f"S{int(match.group(1))}" for match in AXIS_PATTERN.finditer(text)]
    normalized = [axis for axis in matches if axis in AXIS_ORDER_INDEX]
    if normalized:
        return sort_axes(normalized)
    tokens = re.split(r"[,\s/|]+", text)
    parsed = [normalize_axis(token) for token in tokens]
    return sort_axes(token for token in parsed if token)


def legacy_loop_to_axes(text: str | None) -> List[str]:
    if not text:
        return []
    lowered = text.lower()
    lowered = lowered.replace("↑", " ")
    axes: List[str] = []
    for key, values in LEGACY_LOOP_AXIS_MAP.items():
        if key in lowered:
            axes.extend(values)
    return sort_axes(axes)


def ensure_axes(tokens: Iterable[str]) -> List[str]:
    axes = []
    for token in tokens:
        normalized = normalize_axis(token)
        if not normalized:
            raise ValueError(f"invalid systemic axis token '{token}' (expected S1-S10)")
        axes.append(normalized)
    return sort_axes(axes)


def highest_axis_value(axes: Iterable[str]) -> int | None:
    values = []
    for axis in axes:
        normalized = normalize_axis(axis)
        if normalized:
            try:
                values.append(int(normalized[1:]))
            except ValueError:
                continue
    if not values:
        return None
    return max(values)


def derive_layer_targets(primary_layer: str | None, additional: Iterable[str] | None = None) -> List[str]:
    targets: List[str] = []
    if primary_layer:
        layer = primary_layer.strip().upper()
        if layer.startswith("L") and len(layer) == 2 and layer[1].isdigit():
            targets.append(layer)
    if additional:
        for raw in additional:
            layer = raw.strip().upper()
            if layer.startswith("L") and len(layer) == 2 and layer[1].isdigit():
                targets.append(layer)
    return _dedupe_preserve(targets)
