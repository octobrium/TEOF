"""Synthesize backlog items from health signals, audits, and advisories."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, List, Mapping

from tools.autonomy.shared import load_json

ROOT = Path(__file__).resolve().parents[2]
TODO_PATH = ROOT / "_plans" / "next-development.todo.json"
POLICY_PATH = ROOT / "docs" / "automation" / "backlog-policy.json"
GUIDELINE_DIR = ROOT / "docs" / "specs"
SUMMARY_PATH = ROOT / "_report" / "usage" / "external-summary.json"
HYGIENE_GLOB = "_report/usage/autonomy-actions/hygiene-*.json"
HEALTH_OUTPUT_DIR = ROOT / "_report" / "health"
RECEIPT_DIR = ROOT / "_report" / "autonomy" / "backlog-synth"


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


def _remove_items(
    todo: Mapping[str, object], *, predicate: Callable[[Mapping[str, object]], bool]
) -> tuple[Mapping[str, object], List[Mapping[str, object]]]:
    data = dict(todo)
    remaining: List[Mapping[str, object]] = []
    removed: List[Mapping[str, object]] = []
    for raw in _ensure_list(todo.get("items")):
        item = dict(raw)
        if predicate(item):
            removed.append(item)
            continue
        remaining.append(item)
    data["items"] = remaining
    history = list(_ensure_list(data.get("history")))
    data["history"] = history
    return data, removed


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _load_advisories(path: Path) -> List[Mapping[str, object]]:
    payload = load_json(path)
    data = payload if isinstance(payload, Mapping) else None
    if not data:
        return []
    advisories = data.get("advisories")
    return _ensure_list(advisories)


def _advisory_item(advisory: Mapping[str, object], *, plan_hint: str | None = None) -> Mapping[str, object]:
    advisory_id = advisory.get("id")
    if not isinstance(advisory_id, str):
        return {}
    title = advisory.get("claim")
    if not isinstance(title, str) or not title.strip():
        title = f"Address advisory {advisory_id}"
    notes = advisory.get("targets")
    target = notes[0] if isinstance(notes, list) and notes else ""
    evidence = advisory.get("evidence") or {}
    receipts = evidence.get("receipts") if isinstance(evidence, Mapping) else None

    item: dict[str, object] = {
        "id": advisory_id,
        "title": title,
        "status": "pending",
        "source": "fractal-advisory",
    }
    if plan_hint:
        item["plan_suggestion"] = plan_hint
    if isinstance(target, str) and target:
        item["notes"] = f"Target: {target}"
    layer = advisory.get("layer")
    if isinstance(layer, str):
        item["layer"] = layer
    systemic = advisory.get("systemic_scale")
    if systemic is not None:
        item["systemic_scale"] = systemic
    if isinstance(receipts, Iterable):
        rel_receipts = []
        for receipt in receipts:
            if isinstance(receipt, str):
                rel_receipts.append(_relative(Path(receipt)))
        if rel_receipts:
            item["receipts"] = rel_receipts
    source_receipt = advisory.get("source_receipt")
    if isinstance(source_receipt, str):
        item["evidence"] = {"source_receipt": _relative(Path(source_receipt))}
    return item


def _write_receipt(
    *,
    todo_path: Path,
    policy_path: Path,
    health_report: Path,
    advisory_context: List[Mapping[str, object]],
    added: List[Mapping[str, object]],
    removed: List[Mapping[str, object]],
) -> Path:
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = RECEIPT_DIR / f"synth-{timestamp}.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "todo_path": _relative(todo_path),
        "policy_path": _relative(policy_path),
        "health_report": _relative(health_report),
        "advisories": advisory_context,
        "added": added,
        "removed": removed,
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _authenticity_signal() -> Mapping[str, object]:
    raw = load_json(SUMMARY_PATH)
    summary = raw if isinstance(raw, Mapping) else None
    attention_count = 0
    if summary and isinstance(summary.get("feeds"), Mapping):
        for feed in summary["feeds"].values():
            if isinstance(feed, Mapping) and feed.get("trust", {}).get("status") == "attention":
                attention_count += 1
    return {
        "source": _relative(SUMMARY_PATH),
        "attention_feeds": attention_count,
    }


def _latest_hygiene() -> Mapping[str, object] | None:
    reports: List[Path] = sorted(ROOT.glob(HYGIENE_GLOB))
    if not reports:
        return None
    latest = reports[-1]
    raw = load_json(latest)
    data = raw if isinstance(raw, Mapping) else None
    if data is None:
        return None
    result = dict(data)
    result["report_path"] = _relative(latest)
    return result


def emit_health_report() -> Path:
    HEALTH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "generated_at": _iso_now(),
        "authenticity": _authenticity_signal(),
        "hygiene": _latest_hygiene(),
    }
    destination = HEALTH_OUTPUT_DIR / f"health-{_utc_now().strftime('%Y%m%dT%H%M%SZ')}.json"
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination


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
        sanitised = re.sub(r"[^A-Za-z0-9._-]", "_", value).strip("_")
        return sanitised or "unknown"
    return "unknown"


def audit_layers(todo_path: Path = TODO_PATH) -> Path:
    raw = load_json(todo_path)
    todo = raw if isinstance(raw, Mapping) else {}
    layers = _collect_layers()
    gaps: List[str] = []
    for layer in layers:
        if _needs_backlog(todo, layer):
            gaps.append(layer)
    audit_dir = ROOT / "_report" / "usage" / "autonomy-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": todo.get("updated"),
        "layers": layers,
        "gaps": gaps,
        "todo_path": _relative(todo_path) if todo_path.exists() else None,
    }
    slug = _timestamp_slug(todo.get("updated"))
    path = audit_dir / f"audit-{slug}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


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
    health_report = emit_health_report()
    raw_health = load_json(health_report)
    health: Mapping[str, object] = raw_health if isinstance(raw_health, Mapping) else {}

    added: List[Mapping[str, object]] = []
    removed: List[Mapping[str, object]] = []
    advisory_receipts: List[Mapping[str, object]] = []
    for rule in rules:
        rule_id = rule.get("id")
        backlog_id = rule.get("backlog_id") if isinstance(rule.get("backlog_id"), str) else None

        if rule_id == "AUTH-ATTENTION":
            if backlog_id is None or _has_item(updated, backlog_id):
                continue
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
            continue
        if rule_id == "HYGIENE-SIZE":
            if backlog_id is None or _has_item(updated, backlog_id):
                continue
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
            continue
        if rule_id == "FRACTAL-ADVISORY":
            conditions = rule.get("conditions") if isinstance(rule.get("conditions"), Mapping) else {}
            advisory_path_raw = conditions.get("advisories") if isinstance(conditions, Mapping) else None
            if isinstance(advisory_path_raw, str) and advisory_path_raw:
                advisory_path = Path(advisory_path_raw)
                if not advisory_path.is_absolute():
                    advisory_path = ROOT / advisory_path
            else:
                advisory_path = ROOT / "_report" / "fractal" / "advisories" / "latest.json"
            advisories = _load_advisories(advisory_path)
            current_ids: set[str] = set()
            added_ids: List[str] = []
            for advisory in advisories:
                advisory_id = advisory.get("id")
                if not isinstance(advisory_id, str):
                    continue
                current_ids.add(advisory_id)
                if _has_item(updated, advisory_id):
                    continue
                item = _advisory_item(advisory, plan_hint=rule.get("plan_suggestion"))
                if not item:
                    continue
                updated = _append_item(updated, item)
                added.append(item)
                added_ids.append(advisory_id)
            removed_ids: List[str] = []
            if current_ids:
                updated, removed_items = _remove_items(
                    updated,
                    predicate=lambda item: (
                        isinstance(item.get("id"), str)
                        and (
                            str(item["id"]).startswith("ADV-")
                            or item.get("source") == "fractal-advisory"
                        )
                        and str(item["id"]) not in current_ids
                    ),
                )
            else:
                updated, removed_items = _remove_items(
                    updated,
                    predicate=lambda item: (
                        isinstance(item.get("id"), str)
                        and (
                            str(item["id"]).startswith("ADV-")
                            or item.get("source") == "fractal-advisory"
                        )
                    ),
                )
            if removed_items:
                removed.extend(removed_items)
                for entry in removed_items:
                    entry_id = entry.get("id")
                    if isinstance(entry_id, str):
                        removed_ids.append(entry_id)
            advisory_receipts.append(
                {
                    "rule_id": rule_id,
                    "path": _relative(advisory_path),
                    "total": len(advisories),
                    "added": added_ids,
                    "removed": removed_ids,
                }
            )

    receipt_path: Path | None = None
    if added or removed:
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        updated["updated"] = timestamp
        todo_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipt_path = _write_receipt(
            todo_path=todo_path,
            policy_path=policy_path,
            health_report=health_report,
            advisory_context=[
                ctx
                for ctx in advisory_receipts
                if ctx.get("added") or ctx.get("removed")
            ],
            added=added,
            removed=removed,
        )
    result: dict[str, object] = {
        "todo_path": _relative(todo_path),
        "policy_path": _relative(policy_path),
        "added": added,
        "removed": removed,
        "health_report": _relative(health_report),
    }
    if receipt_path is not None:
        result["receipt_path"] = _relative(receipt_path)
    return result


__all__ = ["synthesise", "emit_health_report", "audit_layers"]
