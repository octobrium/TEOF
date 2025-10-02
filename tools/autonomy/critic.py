"""Critic/anomaly detection loop for backlog, tasks, and memory facts."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from tools.autonomy.shared import load_json, normalise_layer, normalise_scale

ROOT = Path(__file__).resolve().parents[2]
BACKLOG_PATH = ROOT / "_plans" / "next-development.todo.json"
TASKS_PATH = ROOT / "agents" / "tasks" / "tasks.json"
STATE_PATH = ROOT / "memory" / "state.json"
CLAIMS_DIR = ROOT / "_bus" / "claims"


def _load_backlog() -> list[dict[str, Any]]:
    data = load_json(BACKLOG_PATH)
    items = data.get("items") if isinstance(data, dict) else None
    return [item for item in items if isinstance(item, dict)] if items else []


def _load_tasks() -> list[dict[str, Any]]:
    data = load_json(TASKS_PATH)
    items = data.get("tasks") if isinstance(data, dict) else None
    return [item for item in items if isinstance(item, dict)] if items else []


def _load_facts() -> list[dict[str, Any]]:
    data = load_json(STATE_PATH)
    items = data.get("facts") if isinstance(data, dict) else None
    return [item for item in items if isinstance(item, dict)] if items else []


def _detect_missing_receipts(backlog: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    for item in backlog:
        status = (item.get("status") or "").lower()
        if status not in {"pending", "blocked", "active"}:
            continue
        receipts = [r for r in (item.get("receipts") or []) if isinstance(r, str)]
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


def _git_commit() -> str | None:
    head = ROOT / ".git" / "HEAD"
    if not head.exists():
        return None
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def _state_snapshot() -> dict[str, int]:
    log_path = ROOT / "memory" / "log.jsonl"
    logs = 0
    if log_path.exists():
        with log_path.open(encoding="utf-8") as handle:
            for _ in handle:
                logs += 1
    facts = len(_load_facts())
    return {"log_entries": logs, "facts": facts}


def write_receipt(anomalies: Sequence[dict[str, Any]], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": _git_commit(),
        "state_snapshot": _state_snapshot(),
        "anomalies": list(anomalies),
    }
    base = json.dumps(payload, ensure_ascii=False, indent=2)
    checksum = hashlib.sha256(base.encode("utf-8")).hexdigest()
    payload["receipt_sha256"] = checksum
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def _emit_bus_claim(anomaly: dict[str, Any], receipt_path: Path) -> Path:
    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)
    task = anomaly.get("suggested_task") or {}
    task_id = str(task.get("task_id") or f"REPAIR-{anomaly.get('id')}")
    filename = f"{task_id}.json"
    claim_path = CLAIMS_DIR / filename
    if claim_path.exists():
        return claim_path
    payload = {
        "task_id": task_id,
        "status": "pending",
        "agent_id": "critic",
        "plan_id": anomaly.get("id"),
        "branch": f"agent/critic/{task_id.lower()}",
        "note": anomaly.get("title"),
        "receipt": str(receipt_path.relative_to(ROOT)),
    }
    claim_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return claim_path


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
            claim_path = _emit_bus_claim(anomaly, receipt_path)
            emitted.append(claim_path.relative_to(ROOT).as_posix())
        if emitted:
            print("emitted bus claims:")
            for path in emitted:
                print(f"  - {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
