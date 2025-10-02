"""Shared helpers for autonomy tooling."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    """Read JSON from *path*, returning ``None`` when missing or invalid."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def normalise_layer(value: str | None, *, default: str = "L5") -> str:
    """Return canonical layer code (``L0``–``L6``) with fallback."""

    if not value:
        return default
    val = value.strip().upper()
    if val.startswith("L") and val[1:].isdigit():
        return val
    return default


def normalise_scale(value: Any, layer: str, *, lower: int = 1, upper: int = 10) -> int:
    """Normalise systemic scale (1–10) using *layer* as a hint."""

    if isinstance(value, int) and lower <= value <= upper:
        return value
    try:
        layer_num = int(layer[1:]) if layer.startswith("L") else 5
    except ValueError:
        layer_num = 5
    return max(lower, min(upper, 4 + layer_num))


__all__ = ["load_json", "normalise_layer", "normalise_scale"]
