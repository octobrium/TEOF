"""Audit backlog alignment with TEOF guidelines (L0-L6)."""
from __future__ import annotations

import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Mapping

from tools.autonomy.shared import load_json

ROOT = Path(__file__).resolve().parents[2]
GUIDELINE_DIR = ROOT / "docs" / "specs"
AUDIT_DIR = ROOT / "_report" / "usage" / "autonomy-audit"
TODO_PATH = ROOT / "_plans" / "next-development.todo.json"


def _collect_layers() -> List[str]:
    layers: List[str] = []
    for file in GUIDELINE_DIR.glob("*.md"):
        layers.append(file.stem)
    return sorted(layers)


def _needs_backlog(todo: Mapping[str, object], layer: str) -> bool:
    for item in todo.get("items", []):
        if isinstance(item, Mapping) and item.get("layer") == layer and item.get("status") != "done":
            return False
    return True


def _timestamp_slug(value: object) -> str:
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
            try:
                ts = datetime.strptime(value, fmt)
            except ValueError:
                continue
            return ts.strftime("%Y%m%dT%H%M%SZ")
        sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", value).strip("_")
        return sanitized or "unknown"
    return "unknown"


def audit_layers(todo_path: Path = TODO_PATH) -> Path:
    raw = load_json(todo_path)
    todo = raw if isinstance(raw, Mapping) else {}
    layers = _collect_layers()
    gaps: List[str] = []
    for layer in layers:
        if _needs_backlog(todo, layer):
            gaps.append(layer)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": todo.get("updated"),
        "layers": layers,
        "gaps": gaps,
    }
    if todo_path.exists():
        try:
            rel = todo_path.relative_to(ROOT)
        except ValueError:
            rel = todo_path
        report["todo_path"] = str(rel)
    else:
        report["todo_path"] = None

    slug = _timestamp_slug(todo.get("updated"))
    path = AUDIT_DIR / f"audit-{slug}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


__all__ = ["audit_layers"]
