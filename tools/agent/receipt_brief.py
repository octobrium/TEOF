"""Produce human-readable summaries for plans and backlog items."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Mapping, Sequence

from tools.autonomy.receipt_utils import (
    collect_plan_receipts,
    load_plan,
    normalise_receipts,
    resolve_item_receipts,
)
from tools.autonomy.shared import load_backlog_items, write_receipt_payload

ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = ROOT / "_plans"
BACKLOG_PATH = PLANS_DIR / "next-development.todo.json"
DEFAULT_OUT_DIR = ROOT / "_report" / "usage" / "receipt-briefs"


def _load_backlog_item(item_id: str) -> Mapping[str, object]:
    entries = load_backlog_items(BACKLOG_PATH, include_archive=True)
    for entry in entries:
        if isinstance(entry, Mapping) and entry.get("id") == item_id:
            return entry
    raise KeyError(f"backlog item not found: {item_id}")


def _format_plan_brief(plan_id: str, plan: Mapping[str, object]) -> str:
    summary = str(plan.get("summary") or "").strip()
    status = str(plan.get("status") or "unknown")
    layer = str(plan.get("layer") or plan.get("layer_targets") or "")
    systemic_targets = plan.get("systemic_targets") or []
    systemic_str = ", ".join(str(target) for target in systemic_targets) if systemic_targets else "None"
    scale = plan.get("systemic_scale")
    header = f"Plan {plan_id} — status: {status}"
    if layer:
        if isinstance(layer, Sequence) and not isinstance(layer, str):
            layer = "/".join(str(value) for value in layer)
        header += f"; layer: {layer}"
    if scale:
        header += f"; systemic scale: {scale}"
    header += f"; systemic targets: {systemic_str}"
    lines = [header]
    if summary:
        lines.append(f"Summary: {summary}")

    steps = plan.get("steps", []) or []
    if steps:
        lines.append("Steps:")
        for step in steps:
            if not isinstance(step, Mapping):
                continue
            step_id = step.get("id") or step.get("title") or "unnamed"
            step_status = step.get("status") or "unknown"
            title = step.get("title") or ""
            notes = step.get("notes") or ""
            lines.append(f"  - {step_id} [{step_status}] {title}".rstrip())
            if notes:
                lines.append(f"      notes: {notes}")
            step_receipts = normalise_receipts(step.get("receipts"))
            if step_receipts:
                lines.append(f"      receipts: {', '.join(step_receipts)}")

    receipts = collect_plan_receipts(plan_id)
    lines.append(f"Receipts ({len(receipts)}): {', '.join(receipts) if receipts else 'None'}")
    checkpoint = plan.get("checkpoint")
    if isinstance(checkpoint, Mapping):
        checkpoint_status = checkpoint.get("status")
        checkpoint_desc = checkpoint.get("description")
        lines.append(f"Checkpoint: {checkpoint_status} — {checkpoint_desc}")
    return "\n".join(lines)


def _format_backlog_brief(item_id: str, item: Mapping[str, object]) -> str:
    title = item.get("title") or "(untitled)"
    status = item.get("status") or "unknown"
    plan_id = item.get("plan_suggestion") or "N/A"
    priority = item.get("priority")
    layer = item.get("layer")
    systemic_scale = item.get("systemic_scale")
    notes = item.get("notes") or ""
    receipts = resolve_item_receipts(item)
    receipts_ref = item.get("receipts_ref")
    header = f"Backlog {item_id} — {title} (status: {status})"
    lines = [header]
    lines.append(f"  plan: {plan_id}")
    if priority:
        lines.append(f"  priority: {priority}")
    if layer:
        lines.append(f"  layer: {layer}")
    if systemic_scale:
        lines.append(f"  systemic scale: {systemic_scale}")
    if notes:
        lines.append(f"  notes: {notes}")
    if receipts:
        lines.append(f"  receipts ({len(receipts)}): {', '.join(receipts)}")
    if isinstance(receipts_ref, Mapping):
        details = []
        if "kind" in receipts_ref:
            details.append(f"kind={receipts_ref['kind']}")
        if "plan_id" in receipts_ref:
            details.append(f"plan={receipts_ref['plan_id']}")
        if "count" in receipts_ref:
            details.append(f"count={receipts_ref['count']}")
        if "digest" in receipts_ref:
            details.append(f"digest={receipts_ref['digest'][:12]}")
        if details:
            lines.append(f"  receipts_ref: {', '.join(details)}")
    completed_at = item.get("completed_at")
    if completed_at:
        lines.append(f"  completed_at: {completed_at}")
    return "\n".join(lines)


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_brief(path: Path, payload: str) -> None:
    _ensure_dir(path)
    path.write_text(payload + "\n", encoding="utf-8")


def _default_out_path(kind: str, identifier: str) -> Path:
    file_name = f"{kind}-{identifier}.md"
    return DEFAULT_OUT_DIR / file_name


def _emit_receipt(path: Path, *, kind: str, identifier: str, brief: str) -> None:
    write_receipt_payload(
        path,
        {
            "kind": kind,
            "identifier": identifier,
            "brief": brief,
        },
    )


def generate_plan_brief(plan_id: str) -> str:
    plan = load_plan(plan_id)
    return _format_plan_brief(plan_id, plan)


def generate_backlog_brief(item_id: str) -> str:
    item = _load_backlog_item(item_id)
    return _format_backlog_brief(item_id, item)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="append", dest="plans", help="Plan identifier to summarise")
    parser.add_argument("--backlog", action="append", dest="backlog_items", help="Backlog item identifier to summarise")
    parser.add_argument("--write", action="store_true", help="Write markdown briefs under _report/usage/receipt-briefs/")
    parser.add_argument(
        "--receipt",
        type=Path,
        help="Optional JSON receipt output (captures the generated brief for auditing)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout output")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    emitted_any = False

    identifiers: List[tuple[str, str]] = []
    for plan_id in args.plans or []:
        identifiers.append(("plan", plan_id))
    for item_id in args.backlog_items or []:
        identifiers.append(("backlog", item_id))

    if not identifiers:
        raise SystemExit("::error:: provide at least one --plan or --backlog identifier")

    briefs: List[Mapping[str, str]] = []
    for kind, identifier in identifiers:
        if kind == "plan":
            brief = generate_plan_brief(identifier)
        else:
            brief = generate_backlog_brief(identifier)
        briefs.append({"kind": kind, "id": identifier, "brief": brief})
        if not args.quiet:
            print(brief)
            print()
        if args.write:
            out_path = _default_out_path(kind, identifier)
            _write_brief(out_path, brief)
            emitted_any = True

    if args.receipt:
        _emit_receipt(args.receipt, kind="receipt_brief", identifier=";".join(f"{b['kind']}:{b['id']}" for b in briefs), brief="\n\n".join(b["brief"] for b in briefs))
        emitted_any = True

    return 0 if (briefs or emitted_any) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
