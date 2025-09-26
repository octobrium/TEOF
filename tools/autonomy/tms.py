"""Truth maintenance loop for detecting fact contradictions."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "memory" / "state.json"
PLANS_DIR = ROOT / "_plans"


def _load_state() -> list[dict[str, Any]]:
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    facts = data.get("facts") if isinstance(data, dict) else None
    return [fact for fact in facts if isinstance(fact, dict)] if facts else []


def _normalise_layer(layer: str | None) -> str:
    value = (layer or "L4").strip().upper()
    if value.startswith("L") and value[1:].isdigit():
        return value
    return "L4"


def _normalise_scale(value: Any, layer: str) -> int:
    if isinstance(value, int) and 1 <= value <= 10:
        return value
    try:
        layer_num = int(layer[1:]) if layer.startswith("L") else 4
    except ValueError:
        layer_num = 4
    return max(1, min(10, 4 + layer_num))


def detect_conflicts() -> list[dict[str, Any]]:
    facts = _load_state()
    conflicts: list[dict[str, Any]] = []
    by_id: dict[str, list[dict[str, Any]]] = {}
    for fact in facts:
        identifier = str(fact.get("id") or "")
        by_id.setdefault(identifier, []).append(fact)

    for identifier, group in by_id.items():
        if not identifier or len(group) < 2:
            continue
        statements = {str(item.get("statement")) for item in group}
        layers = {_normalise_layer(item.get("layer")) for item in group}
        if len(statements) <= 1 and len(layers) <= 1:
            continue
        first = group[0]
        layer = _normalise_layer(first.get("layer"))
        scale = _normalise_scale(first.get("systemic_scale"), layer)
        conflicts.append(
            {
                "type": "conflicting_facts",
                "id": identifier,
                "statements": list(statements),
                "coord": {"layer": layer, "systemic_scale": scale},
                "facts": [
                    {
                        "statement": item.get("statement"),
                        "confidence": item.get("confidence"),
                        "source_run": item.get("source_run"),
                    }
                    for item in group
                ],
                "suggested_plan": {
                    "plan_id": f"TMS-{identifier}",
                    "summary": f"Resolve contradictory fact {identifier}",
                    "layer": layer,
                    "systemic_scale": scale,
                },
            }
        )
    for fact in facts:
        try:
            confidence = float(fact.get("confidence"))
        except (TypeError, ValueError):
            continue
        if confidence >= 0.4:
            continue
        identifier = str(fact.get("id") or "")
        statement = str(fact.get("statement") or identifier)
        layer = _normalise_layer(fact.get("layer"))
        scale = _normalise_scale(fact.get("systemic_scale"), layer)
        conflicts.append(
            {
                "type": "low_confidence_fact",
                "id": identifier,
                "statements": [statement],
                "coord": {"layer": layer, "systemic_scale": scale},
                "facts": [
                    {
                        "statement": statement,
                        "confidence": confidence,
                        "source_run": fact.get("source_run"),
                    }
                ],
                "suggested_plan": {
                    "plan_id": f"TMS-{identifier or 'fact'}-confidence",
                    "summary": f"Boost confidence for fact {identifier or statement}",
                    "layer": layer,
                    "systemic_scale": scale,
                },
            }
        )
    return conflicts


def render_table(conflicts: Sequence[dict[str, Any]]) -> str:
    if not conflicts:
        return "(no conflicts detected)"
    headers = ["Type", "ID", "Coord", "Statements"]
    rows = []
    for conflict in conflicts:
        coord = conflict.get("coord", {})
        coord_str = f"S{coord.get('systemic_scale', '?')}:{coord.get('layer', '?')}"
        statements = conflict.get("statements", [])
        rows.append([
            conflict.get("type", ""),
            conflict.get("id", ""),
            coord_str,
            "; ".join(statements)[:80],
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


def _git_commit() -> str | None:
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
    log_count = 0
    if log_path.exists():
        with log_path.open(encoding="utf-8") as handle:
            for _ in handle:
                log_count += 1
    return {"log_entries": log_count, "facts": len(_load_state())}


def write_receipt(conflicts: Sequence[dict[str, Any]], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": _git_commit(),
        "state_snapshot": _state_snapshot(),
        "conflicts": list(conflicts),
    }
    base = json.dumps(payload, ensure_ascii=False, indent=2)
    checksum = hashlib.sha256(base.encode("utf-8")).hexdigest()
    payload["receipt_sha256"] = checksum
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def _emit_plan(conflict: dict[str, Any], receipt_path: Path) -> Path:
    skeleton = {
        "version": 0,
        "plan_id": conflict.get("suggested_plan", {}).get("plan_id"),
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor": "tms",
        "summary": conflict.get("suggested_plan", {}).get("summary"),
        "status": "pending",
        "layer": conflict.get("coord", {}).get("layer"),
        "systemic_scale": conflict.get("coord", {}).get("systemic_scale"),
        "receipts": [str(receipt_path.relative_to(ROOT))],
        "steps": [],
    }
    plan_id = skeleton["plan_id"] or f"TMS-{conflict.get('id') or 'conflict'}"
    filename = f"{plan_id}.plan.json"
    plan_path = PLANS_DIR / filename
    if plan_path.exists():
        return plan_path
    plan_path.write_text(json.dumps(skeleton, indent=2) + "\n", encoding="utf-8")
    return plan_path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Output format")
    parser.add_argument("--out", type=Path, help="Optional path to write TMS receipt JSON")
    parser.add_argument("--emit-plan", action="store_true", help="Emit plan skeletons for conflicts")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    conflicts = detect_conflicts()
    if args.format == "json":
        print(json.dumps(conflicts, ensure_ascii=False, indent=2))
    else:
        print(render_table(conflicts))

    receipt_path = None
    if args.out:
        out_path = args.out if args.out.is_absolute() else ROOT / args.out
        receipt_path = write_receipt(conflicts, out_path)
        print(f"wrote receipt → {receipt_path.relative_to(ROOT)}")

    if args.emit_plan:
        if receipt_path is None:
            print("::error:: --emit-plan requires --out for provenance")
            return 2
        emitted = []
        for conflict in conflicts:
            plan_path = _emit_plan(conflict, receipt_path)
            emitted.append(plan_path.relative_to(ROOT).as_posix())
        if emitted:
            print("emitted plans:")
            for path in emitted:
                print(f"  - {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
