"""Audit backlog alignment with TEOF guidelines (L0-L6)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Mapping

ROOT = Path(__file__).resolve().parents[2]
GUIDELINE_DIR = ROOT / "docs" / "specs"
AUDIT_DIR = ROOT / "_report" / "usage" / "autonomy-audit"
TODO_PATH = ROOT / "_plans" / "next-development.todo.json"


def _load_json(path: Path) -> Mapping[str, object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


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


def audit_layers(todo_path: Path = TODO_PATH) -> Path:
    todo = _load_json(todo_path) or {}
    layers = _collect_layers()
    gaps: List[str] = []
    for layer in layers:
        if _needs_backlog(todo, layer):
            gaps.append(layer)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": Path("report").absolute(),
    }
    report = {
        "generated_at": todo.get("updated"),
        "layers": layers,
        "gaps": gaps,
        "todo_path": str(todo_path.relative_to(ROOT)) if todo_path.exists() else None,
    }
    path = AUDIT_DIR / f"audit-{todo.get('updated', 'unknown')}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


__all__ = ["audit_layers"]
