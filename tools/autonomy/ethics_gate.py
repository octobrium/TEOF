"""L6 ethics gate to ensure high-risk items have guard receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[2]
BACKLOG_PATH = ROOT / "_plans" / "next-development.todo.json"
TASKS_PATH = ROOT / "agents" / "tasks" / "tasks.json"
CLAIMS_DIR = ROOT / "_bus" / "claims"

GUARD_KEYWORDS = ("consent", "review", "ethics")
HIGH_RISK_LAYERS = {"L6"}
HIGH_RISK_SCALE_THRESHOLD = 8


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _normalise_layer(value: str | None) -> str:
    if not value:
        return "L5"
    val = value.strip().upper()
    if val.startswith("L") and val[1:].isdigit():
        return val
    return "L5"


def _normalise_scale(value: Any, layer: str) -> int:
    if isinstance(value, int) and 1 <= value <= 10:
        return value
    try:
        layer_num = int(layer[1:]) if layer.startswith("L") else 5
    except ValueError:
        layer_num = 5
    return max(1, min(10, 4 + layer_num))


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


def _extract_receipts(item: dict[str, Any]) -> list[str]:
    receipts = item.get("receipts")
    if not isinstance(receipts, list):
        return []
    return [r for r in receipts if isinstance(r, str)]


def detect_violations() -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    backlog_data = _load_json(BACKLOG_PATH)
    backlog_items = backlog_data.get("items") if isinstance(backlog_data, dict) else None
    if isinstance(backlog_items, list):
        for item in backlog_items:
            if not isinstance(item, dict):
                continue
            layer = _normalise_layer(item.get("layer"))
            scale = _normalise_scale(item.get("systemic_scale"), layer)
            if not _is_high_risk(item, layer, scale):
                continue
            receipts = _extract_receipts(item)
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

    tasks_data = _load_json(TASKS_PATH)
    tasks = tasks_data.get("tasks") if isinstance(tasks_data, dict) else None
    if isinstance(tasks, list):
        for task in tasks:
            if not isinstance(task, dict):
                continue
            layer = _normalise_layer(task.get("layer"))
            scale = _normalise_scale(task.get("systemic_scale"), layer)
            if not _is_high_risk(task, layer, scale):
                continue
            receipts = _extract_receipts(task)
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


def write_receipt(violations: Sequence[dict[str, Any]], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": _git_commit(),
        "violations": list(violations),
    }
    base = json.dumps(payload, ensure_ascii=False, indent=2)
    checksum = hashlib.sha256(base.encode("utf-8")).hexdigest()
    payload["receipt_sha256"] = checksum
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def _emit_bus_claim(violation: dict[str, Any], receipt_path: Path) -> Path:
    CLAIMS_DIR.mkdir(parents=True, exist_ok=True)
    identifier = str(violation.get("id") or violation.get("title") or "item")
    task_id = f"ETHICS-{identifier}".replace(" ", "-")
    claim_path = CLAIMS_DIR / f"{task_id}.json"
    if claim_path.exists():
        return claim_path
    payload = {
        "task_id": task_id,
        "status": "pending",
        "agent_id": "ethics_gate",
        "plan_id": violation.get("id"),
        "branch": f"agent/ethics/{task_id.lower()}",
        "note": violation.get("title"),
        "receipt": str(receipt_path.relative_to(ROOT)),
    }
    claim_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return claim_path


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
            claim_path = _emit_bus_claim(violation, receipt_path)
            emitted.append(claim_path.relative_to(ROOT).as_posix())
        if emitted:
            print("emitted bus claims:")
            for path in emitted:
                print(f"  - {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
