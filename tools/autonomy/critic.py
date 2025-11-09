"""Critic/anomaly detection loop for backlog items and memory facts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from teof._paths import repo_root

from tools.autonomy.receipt_utils import resolve_item_receipts
from tools.autonomy.shared import (
    count_lines,
    git_commit,
    load_backlog_items,
    load_state_facts,
    normalise_layer,
    normalise_scale,
    utc_timestamp,
    write_receipt_payload,
)
from tools.autonomy import shared_bus

ROOT = repo_root(default=Path(__file__).resolve().parents[2])
CLAIMS_DIR = ROOT / "_bus" / "claims"  # legacy attribute (tests monkeypatch)
BACKLOG_PATH = ROOT / "_plans" / "next-development.todo.json"
STATE_PATH = ROOT / "memory" / "state.json"


def _load_backlog() -> list[dict[str, Any]]:
    return load_backlog_items(BACKLOG_PATH)


def _load_facts() -> list[dict[str, Any]]:
    return load_state_facts(STATE_PATH)


def _detect_missing_receipts(backlog: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    for item in backlog:
        status = (item.get("status") or "").lower()
        if status not in {"pending", "blocked", "active"}:
            continue
        receipts = resolve_item_receipts(item)
        if receipts:
            continue
        identifier = str(item.get("id") or "")
        title = str(item.get("title") or identifier)
        layer = normalise_layer(item.get("layer"), default="L5")
        scale = normalise_scale(item.get("systemic_scale"), layer)
        anomalies.append(
            {
                "type": "missing_receipts",
                "id": identifier,
                "title": title,
                "coord": {"layer": layer, "systemic_scale": scale},
                "details": {"status": status},
                "suggested_task": {
                    "task_id": f"REPAIR-{identifier or 'backlog'}",
                    "summary": f"Add receipts for backlog item {identifier or title}",
                    "layer": layer,
                    "systemic_scale": scale,
                },
            }
        )
    return anomalies


def _detect_low_confidence_facts(facts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    for fact in facts:
        try:
            confidence = float(fact.get("confidence"))
        except (TypeError, ValueError):
            continue
        if confidence >= 0.5:
            continue
        identifier = str(fact.get("id") or "")
        statement = str(fact.get("statement") or identifier)
        layer = normalise_layer(fact.get("layer"), default="L2")
        scale = normalise_scale(fact.get("systemic_scale"), layer)
        anomalies.append(
            {
                "type": "low_confidence_fact",
                "id": identifier,
                "title": statement,
                "coord": {"layer": layer, "systemic_scale": scale},
                "details": {"confidence": confidence},
                "suggested_task": {
                    "task_id": f"REPAIR-FACT-{identifier or 'unknown'}",
                    "summary": f"Boost confidence for fact {identifier or statement}",
                    "layer": layer,
                    "systemic_scale": scale,
                },
            }
        )
    return anomalies


def detect_anomalies() -> list[dict[str, Any]]:
    backlog = _load_backlog()
    facts = _load_facts()
    anomalies: list[dict[str, Any]] = []
    anomalies.extend(_detect_missing_receipts(backlog))
    anomalies.extend(_detect_low_confidence_facts(facts))
    return anomalies


def _state_snapshot() -> dict[str, int]:
    log_path = ROOT / "memory" / "log.jsonl"
    facts = len(_load_facts())
    return {"log_entries": count_lines(log_path), "facts": facts}


def write_receipt(anomalies: Sequence[dict[str, Any]], out_path: Path) -> Path:
    payload = {
        "generated_at": utc_timestamp(),
        "git_commit": git_commit(ROOT),
        "state_snapshot": _state_snapshot(),
        "anomalies": list(anomalies),
    }
    return write_receipt_payload(out_path, payload)


def emit_bus_claim(anomaly: dict[str, Any], receipt_path: Path) -> Path:
    task = anomaly.get("suggested_task") or {}
    task_id = str(task.get("task_id") or f"REPAIR-{anomaly.get('id') or 'anomaly'}")
    return shared_bus.emit_claim(
        task_id=task_id,
        agent_id="critic",
        note=anomaly.get("title"),
        plan_id=anomaly.get("id"),
        receipt_path=receipt_path,
        branch=f"agent/critic/{task_id.lower()}",
        root=ROOT,
    )


# Backwards compatibility: retain the private alias until downstream callers migrate.
_emit_bus_claim = emit_bus_claim


def render_table(anomalies: Sequence[dict[str, Any]]) -> str:
    if not anomalies:
        return "(no anomalies detected)"
    headers = ["Type", "ID", "Coord", "Summary"]
    rows = []
    for anomaly in anomalies:
        coord = anomaly.get("coord", {})
        coord_str = f"S{coord.get('systemic_scale', '?')}:{coord.get('layer', '?')}"
        rows.append([
            anomaly.get("type", ""),
            anomaly.get("id", ""),
            coord_str,
            (anomaly.get("title") or "")[:60],
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Output format")
    parser.add_argument("--out", type=Path, help="Optional path to write receipt JSON")
    parser.add_argument("--emit-bus", action="store_true", help="Emit repair tasks into _bus/claims")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    anomalies = detect_anomalies()
    if args.format == "json":
        print(json.dumps(anomalies, ensure_ascii=False, indent=2))
    else:
        print(render_table(anomalies))
    receipt_path = None
    if args.out:
        out_path = args.out if args.out.is_absolute() else ROOT / args.out
        receipt_path = write_receipt(anomalies, out_path)
        print(f"wrote receipt → {receipt_path.relative_to(ROOT)}")
    if args.emit_bus and receipt_path is not None:
        emitted = []
        for anomaly in anomalies:
            claim_path = emit_bus_claim(anomaly, receipt_path)
            emitted.append(claim_path.relative_to(ROOT).as_posix())
        if emitted:
            print("emitted bus claims:")
            for path in emitted:
                print(f"  - {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
