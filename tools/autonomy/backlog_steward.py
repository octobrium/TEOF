"""Backlog steward helper.

Inspects `_plans/next-development.todo.json`, compares entries against
their referenced plans, and (optionally) updates the backlog with
receipt-backed completions. Generates a receipt describing the actions
it took so auditors can review the changes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from tools.autonomy.receipt_utils import collect_plan_receipts, compute_receipt_digest
from tools.autonomy.shared import backlog_archive_path, load_json, write_receipt_payload


DEFAULT_BACKLOG = Path("_plans/next-development.todo.json")
DEFAULT_PLANS_DIR = Path("_plans")
DEFAULT_OUT_DIR = Path("_report/usage/backlog-steward")


def _utc_now() -> str:
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_plan(plans_dir: Path, plan_id: str) -> Dict[str, Any] | None:
    if not plan_id:
        return None
    plan_path = plans_dir / f"{plan_id}.plan.json"
    if not plan_path.exists():
        return None
    data = load_json(plan_path)
    return data if isinstance(data, dict) else None


def _plan_completed(plan: Dict[str, Any]) -> bool:
    if plan.get("status") == "done":
        return True
    steps = plan.get("steps", [])
    return bool(steps) and all(isinstance(step, dict) and step.get("status") == "done" for step in steps)


def _update_backlog_item(
    item: Dict[str, Any],
    plan_id: str,
    plan: Dict[str, Any],
    *,
    plans_dir: Path,
) -> Dict[str, Any] | None:
    if not _plan_completed(plan):
        return None
    new_item = dict(item)
    current_status = str(new_item.get("status", ""))
    receipts = collect_plan_receipts(plan_id, plans_dir=plans_dir)
    changed = False

    if current_status.lower() != "done":
        new_item["status"] = "done"
        changed = True

    if new_item.get("receipts") is not None:
        new_item.pop("receipts")
        changed = True

    ref_payload = {
        "kind": "plan",
        "plan_id": plan_id,
        "count": len(receipts),
        "digest": compute_receipt_digest(receipts) if receipts else None,
    }
    if ref_payload["digest"] is None:
        ref_payload.pop("digest")
    if new_item.get("receipts_ref") != ref_payload:
        new_item["receipts_ref"] = ref_payload
        changed = True

    if not new_item.get("completed_at"):
        new_item["completed_at"] = _utc_now()
        changed = True

    return new_item if changed else None


def _apply_updates(backlog: Dict[str, Any], updates: Dict[str, Dict[str, Any]]) -> None:
    items = backlog.get("items", [])
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        key = item.get("id")
        if key in updates:
            items[idx] = updates[key]
    backlog["items"] = items
    backlog["updated"] = _utc_now()


def _archive_completed_items(
    backlog: Dict[str, Any],
    backlog_path: Path,
    completed_ids: Iterable[str],
) -> list[str]:
    """Move completed backlog entries into the archive file."""

    targets = {entry for entry in completed_ids if isinstance(entry, str)}
    if not targets:
        return []

    items = backlog.get("items")
    if not isinstance(items, list):
        return []

    remaining: list[Dict[str, Any]] = []
    moved: list[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            remaining.append(item)
            continue
        item_id = item.get("id")
        status = str(item.get("status", "")).lower()
        if item_id in targets and status == "done":
            moved.append(item)
        else:
            remaining.append(item)

    if not moved:
        return []

    backlog["items"] = remaining

    archive_path = backlog_archive_path(backlog_path)
    archive_raw = load_json(archive_path)
    archive = archive_raw if isinstance(archive_raw, Dict) else {}
    archive_items = archive.get("items")
    serialised = (
        [entry for entry in archive_items if isinstance(entry, dict)]
        if isinstance(archive_items, list)
        else []
    )
    serialised = [entry for entry in serialised if entry.get("id") not in targets]
    serialised.extend(moved)

    timestamp = _utc_now()
    archive["version"] = archive.get("version", 0)
    archive["source"] = backlog_path.as_posix()
    archive["items"] = serialised
    archive["count"] = len(serialised)
    archive["exported_at"] = timestamp
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    backlog["archive_ref"] = {
        "path": archive_path.as_posix(),
        "count": archive["count"],
        "exported_at": timestamp,
    }
    backlog["updated"] = timestamp

    return [item.get("id") for item in moved if isinstance(item.get("id"), str)]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backlog", type=Path, default=DEFAULT_BACKLOG, help="Backlog JSON path")
    parser.add_argument("--plans-dir", type=Path, default=DEFAULT_PLANS_DIR, help="Directory containing plan JSON files")
    parser.add_argument("--out", type=Path, help="Receipt output path")
    parser.add_argument("--apply", action="store_true", help="Apply updates to the backlog (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run even if --apply is provided")
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    backlog_path = args.backlog
    plans_dir = args.plans_dir

    backlog = load_json(backlog_path)
    if not isinstance(backlog, dict):
        raise SystemExit(f"::error:: backlog not found or invalid: {backlog_path}")

    items = backlog.get("items", [])
    updates: Dict[str, Dict[str, Any]] = {}
    report: Dict[str, Any] = {
        "generated_at": _utc_now(),
        "backlog": backlog_path.as_posix(),
        "actions": [],
    }

    for item in items:
        if not isinstance(item, dict):
            continue
        plan_id = item.get("plan_suggestion")
        plan = _load_plan(plans_dir, plan_id) if isinstance(plan_id, str) else None
        if not plan:
            continue
        new_item = _update_backlog_item(item, plan_id, plan, plans_dir=plans_dir)
        if new_item is None:
            continue
        updates[item.get("id")] = new_item
        action = {
            "id": item.get("id"),
            "plan_id": plan_id,
            "old_status": item.get("status"),
            "new_status": new_item.get("status"),
            "receipts_ref": new_item.get("receipts_ref"),
        }
        report["actions"].append(action)

    completed_ids = [
        item_id
        for item_id, payload in updates.items()
        if isinstance(item_id, str) and str(payload.get("status", "")).lower() == "done"
    ]

    if not updates:
        if not args.quiet:
            print("backlog_steward: no updates")
        return 0

    apply_updates = args.apply and not args.dry_run

    if apply_updates:
        _apply_updates(backlog, updates)
        archived = _archive_completed_items(backlog, backlog_path, completed_ids)
        _ensure_path(backlog_path)
        backlog_path.write_text(json.dumps(backlog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report["archived_ids"] = archived
        report["applied"] = True
    else:
        report["applied"] = False
        report["archived_ids"] = completed_ids

    out_path = args.out
    if out_path is None:
        out_dir = DEFAULT_OUT_DIR
        _ensure_path(out_dir / "stub")
        timestamp = _utc_now().replace(":", "")
        out_path = out_dir / f"report-{timestamp}.json"
    write_receipt_payload(out_path, report)

    if not args.quiet:
        print(f"backlog_steward: {'applied' if apply_updates else 'suggested'} {len(updates)} update(s)")
        for action in report["actions"]:
            print(f" - {action['id']} -> {action['new_status']} ({action['plan_id']})")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
