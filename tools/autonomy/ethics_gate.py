"""L6 ethics gate to ensure high-risk items have guard receipts."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Sequence

from tools.autonomy.receipt_utils import resolve_item_receipts
from tools.autonomy.shared import (
    git_commit,
    load_backlog_items,
    load_task_items,
    normalise_layer,
    normalise_scale,
    utc_timestamp,
    write_receipt_payload,
)
from tools.autonomy import shared_bus

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"  # legacy attribute (tests monkeypatch)
BACKLOG_PATH = ROOT / "_plans" / "next-development.todo.json"
TASKS_PATH = ROOT / "agents" / "tasks" / "tasks.json"

GUARD_KEYWORDS = ("consent", "review", "ethics")
HIGH_RISK_LAYERS = {"L6"}
HIGH_RISK_SCALE_THRESHOLD = 8
def _is_high_risk(item: dict[str, Any], layer: str, systemic_scale: int) -> bool:
    risk_flag = (item.get("risk") or "").strip().lower()
    if risk_flag == "high":
        return True
    if layer in HIGH_RISK_LAYERS:
        return True
    if systemic_scale >= HIGH_RISK_SCALE_THRESHOLD:
        return True
    title = (item.get("title") or "").lower()
    notes = (item.get("notes") or "").lower()
    if any(keyword in title or keyword in notes for keyword in GUARD_KEYWORDS):
        return True
    return False


def detect_violations() -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    backlog_items = load_backlog_items(BACKLOG_PATH)
    if backlog_items:
        for item in backlog_items:
            layer = normalise_layer(item.get("layer"))
            scale = normalise_scale(item.get("systemic_scale"), layer)
            if not _is_high_risk(item, layer, scale):
                continue
            receipts = resolve_item_receipts(item)
            if _passes_guard(receipts):
                continue
            violations.append(
                {
                    "type": "backlog",
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "coord": {"layer": layer, "systemic_scale": scale},
                    "reason": "missing_guard_receipt",
                    "receipts": receipts,
                }
            )

    tasks = load_task_items(TASKS_PATH)
    if tasks:
        for task in tasks:
            layer = normalise_layer(task.get("layer"))
            scale = normalise_scale(task.get("systemic_scale"), layer)
            if not _is_high_risk(task, layer, scale):
                continue
            receipts = resolve_item_receipts(task)
            if _passes_guard(receipts):
                continue
            violations.append(
                {
                    "type": "task",
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "coord": {"layer": layer, "systemic_scale": scale},
                    "reason": "missing_guard_receipt",
                    "receipts": receipts,
                }
            )
    return violations


def _passes_guard(receipts: list[str]) -> bool:
    for receipt in receipts:
        lowered = receipt.lower()
        if any(keyword in lowered for keyword in GUARD_KEYWORDS):
            return True
    return False


def render_table(violations: Sequence[dict[str, Any]]) -> str:
    if not violations:
        return "(no ethics violations detected)"
    headers = ["Type", "ID", "Coord", "Receipts"]
    rows = []
    for violation in violations:
        coord = violation.get("coord", {})
        coord_str = f"S{coord.get('systemic_scale', '?')}:{coord.get('layer', '?')}"
        receipts = violation.get("receipts") or []
        rows.append([
            violation.get("type", ""),
            violation.get("id", ""),
            coord_str,
            ", ".join(receipts)[:80],
        ])
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(str(cell)))
    fmt = " ".join(f"{{:<{w}}}" for w in widths)
    lines = [fmt.format(*headers), "-" * (sum(widths) + len(widths) - 1)]
    for row in rows:
        lines.append(fmt.format(*row))
    return "\n".join(lines)

def write_receipt(violations: Sequence[dict[str, Any]], out_path: Path) -> Path:
    payload = {
        "generated_at": utc_timestamp(),
        "git_commit": git_commit(ROOT),
        "violations": list(violations),
    }
    return write_receipt_payload(out_path, payload)


def emit_bus_claim(violation: dict[str, Any], receipt_path: Path) -> Path:
    identifier = str(violation.get("id") or violation.get("title") or "item")
    task_id = f"ETHICS-{identifier}"
    return shared_bus.emit_claim(
        task_id=task_id,
        agent_id="ethics_gate",
        note=violation.get("title"),
        plan_id=violation.get("id"),
        receipt_path=receipt_path,
        branch=f"agent/ethics/{task_id.lower()}",
        root=ROOT,
    )


_emit_bus_claim = emit_bus_claim


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Output format")
    parser.add_argument("--out", type=Path, help="Optional path to write ethics receipt JSON")
    parser.add_argument("--emit-bus", action="store_true", help="Emit review claims for each violation")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    violations = detect_violations()
    if args.format == "json":
        print(json.dumps(violations, ensure_ascii=False, indent=2))
    else:
        print(render_table(violations))

    receipt_path = None
    if args.out:
        out_path = args.out if args.out.is_absolute() else ROOT / args.out
        receipt_path = write_receipt(violations, out_path)
        print(f"wrote receipt → {receipt_path.relative_to(ROOT)}")

    if args.emit_bus:
        if receipt_path is None:
            print("::error:: --emit-bus requires --out for provenance")
            return 2
        emitted = []
        for violation in violations:
            claim_path = emit_bus_claim(violation, receipt_path)
            emitted.append(claim_path.relative_to(ROOT).as_posix())
        if emitted:
            print("emitted bus claims:")
            for path in emitted:
                print(f"  - {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
