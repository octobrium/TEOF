"""Synthesize backlog items from health signals."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Mapping

from tools.autonomy import health_sensors
from tools.autonomy.shared import load_json

ROOT = Path(__file__).resolve().parents[2]
TODO_PATH = ROOT / "_plans" / "next-development.todo.json"
POLICY_PATH = ROOT / "docs" / "automation" / "backlog-policy.json"


def _ensure_list(value: object) -> List[Mapping[str, object]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _has_item(todo: Mapping[str, object], backlog_id: str) -> bool:
    for item in _ensure_list(todo.get("items")):
        if item.get("id") == backlog_id:
            return True
    return False


def _append_item(todo: Mapping[str, object], item: Mapping[str, object]) -> Mapping[str, object]:
    data = dict(todo)
    items = list(_ensure_list(data.get("items")))
    items.append(dict(item))
    data["items"] = items
    history = list(_ensure_list(data.get("history")))
    data["history"] = history
    return data


def synthesise(todo_path: Path = TODO_PATH, policy_path: Path = POLICY_PATH) -> Mapping[str, object] | None:
    raw_todo = load_json(todo_path)
    todo = raw_todo if isinstance(raw_todo, Mapping) else None
    if not isinstance(todo, Mapping):
        return None
    raw_policy = load_json(policy_path)
    policy = raw_policy if isinstance(raw_policy, Mapping) else None
    if not isinstance(policy, Mapping):
        return None
    rules = _ensure_list(policy.get("rules"))
    updated = dict(todo)
    health_report = health_sensors.emit_health_report()
    raw_health = load_json(health_report)
    health: Mapping[str, object] = raw_health if isinstance(raw_health, Mapping) else {}

    added: List[Mapping[str, object]] = []
    for rule in rules:
        backlog_id = rule.get("backlog_id")
        if not isinstance(backlog_id, str) or _has_item(updated, backlog_id):
            continue
        if rule.get("id") == "AUTH-ATTENTION":
            attention = int(health.get("authenticity", {}).get("attention_feeds", 0))  # type: ignore[arg-type]
            if attention > 0:
                item = {
                    "id": backlog_id,
                    "title": rule.get("description"),
                    "status": "pending",
                    "plan_suggestion": rule.get("plan_suggestion"),
                    "notes": f"Synthesized due to {attention} attention feeds",
                    "source": "autonomy-synth",
                }
                updated = _append_item(updated, item)
                added.append(item)
        if rule.get("id") == "HYGIENE-SIZE":
            hygiene = health.get("hygiene") or {}
            size_mb = hygiene.get("targets", {}).get("artifacts", {}).get("size_mb") if isinstance(hygiene, Mapping) else None
            try:
                size_val = float(size_mb)
            except (TypeError, ValueError):
                size_val = 0.0
            if size_val >= 5.0:
                item = {
                    "id": backlog_id,
                    "title": rule.get("description"),
                    "status": "pending",
                    "plan_suggestion": rule.get("plan_suggestion"),
                    "notes": f"Synthesized due to artifacts size {size_val}MB",
                    "source": "autonomy-synth",
                }
                updated = _append_item(updated, item)
                added.append(item)

    if added:
        todo_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "todo_path": str(todo_path.relative_to(ROOT)),
        "policy_path": str(policy_path.relative_to(ROOT)),
        "added": added,
        "health_report": str(health_report.relative_to(ROOT)),
    }


__all__ = ["synthesise"]
