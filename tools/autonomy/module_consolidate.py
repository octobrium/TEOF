#!/usr/bin/env python3
"""CLI for autonomy module consolidation (inventory, plan, telemetry scaffolds)."""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.autonomy import shared  # type: ignore  # shared ROOT helpers reused elsewhere

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT_DIR = ROOT / "_report" / "usage" / "autonomy-module-consolidation"
SERVICE_SPEC = {
    "coordination": {
        "target": "tools.autonomy.coord",
        "modules": [
            "tools/autonomy/coordinator_manager.py",
            "tools/autonomy/coordinator_service.py",
            "tools/autonomy/coordinator_guard.py",
            "tools/autonomy/coordinator_worker.py",
            "tools/autonomy/coordinator_loop.py",
            "tools/autonomy/commitment_guard.py",
        ],
    },
    "execution": {
        "target": "tools.autonomy.exec",
        "modules": [
            "tools/autonomy/auto_loop.py",
            "tools/autonomy/conductor.py",
            "tools/autonomy/chronicle.py",
        ],
    },
    "signal": {
        "target": "tools.autonomy.signal",
        "modules": [
            "tools/autonomy/systemic_radar.py",
            "tools/autonomy/autonomy_radar.py",
            "tools/autonomy/objectives_status.py",
            "tools/autonomy/backlog_steward.py",
        ],
    },
    "advisory": {
        "target": "tools.autonomy.advisory",
        "modules": [
            "tools/autonomy/advisory_report.py",
            "tools/autonomy/decision_cycle.py",
            "tools/autonomy/next_step.py",
        ],
    },
}
PRIMITIVE_TOKENS = ("bus_claim(", "bus_event(", "write_receipt", "emit_receipt", "BUS_EMIT")


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _abs_path(path: Path | str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate


def _collect_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for service, spec in SERVICE_SPEC.items():
        modules: list[dict[str, Any]] = []
        primitive_hits = 0
        total_lines = 0
        existing = 0
        for module in spec["modules"]:
            path = ROOT / module
            info = {
                "path": module,
                "exists": path.exists(),
                "lines": 0,
                "primitive_hits": 0,
            }
            if path.exists():
                existing += 1
                try:
                    text = path.read_text(encoding="utf-8")
                except OSError:
                    text = ""
                lines = text.count("\n") + 1 if text else 0
                hits = sum(token in text for token in PRIMITIVE_TOKENS)
                info["lines"] = lines
                info["primitive_hits"] = hits
                primitive_hits += hits
                total_lines += lines
            modules.append(info)
        rows.append(
            {
                "service": service,
                "target": spec["target"],
                "module_count": len(spec["modules"]),
                "existing": existing,
                "line_count": total_lines,
                "primitive_hits": primitive_hits,
                "modules": modules,
            }
        )
    return rows


def cmd_inventory(args: argparse.Namespace) -> int:
    rows = _collect_inventory()
    if args.format == "json":
        print(json.dumps({"generated_at": shared.utc_timestamp(), "services": rows}, ensure_ascii=False, indent=2))
        return 0
    print("Service        Modules  Existing  Lines  Primitive Hits  Target")
    print("-------------- -------  --------  -----  ---------------  ---------------------------")
    for row in rows:
        print(
            f"{row['service']:<14} {row['module_count']:^7}  {row['existing']:^8}  "
            f"{row['line_count']:^5}  {row['primitive_hits']:^15}  {row['target']}"
        )
    return 0


def _selected_services(selected: Sequence[str] | None) -> list[str]:
    if not selected:
        return list(SERVICE_SPEC)
    missing = [svc for svc in selected if svc not in SERVICE_SPEC]
    if missing:
        raise SystemExit(f"unknown service(s): {', '.join(sorted(missing))}")
    return list(dict.fromkeys(selected))


def _timestamp_slug() -> str:
    stamp = shared.utc_timestamp()
    return stamp.replace("-", "").replace(":", "").replace("T", "")


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _ensure_receipt_dir(value: str | None = None) -> Path:
    path = _abs_path(value or DEFAULT_RECEIPT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_plan(path: Path, services: list[str], inventory: list[dict[str, Any]]) -> tuple[Path, Mapping[str, Any]]:
    plan = {
        "schema": "autonomy.module_consolidation.plan/v1",
        "generated_at": shared.utc_timestamp(),
        "services": [],
    }
    index = {row["service"]: row for row in inventory}
    for service in services:
        row = index[service]
        plan["services"].append(
            {
                "service": service,
                "target": SERVICE_SPEC[service]["target"],
                "modules": row["modules"],
                "metrics": {
                    "line_count": row["line_count"],
                    "primitive_hits": row["primitive_hits"],
                },
            }
        )
    _write_json(path, plan)
    return path, plan


def cmd_plan(args: argparse.Namespace) -> int:
    services = _selected_services(args.service)
    inventory = _collect_inventory()
    receipt_dir = _ensure_receipt_dir(args.receipt_dir)
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = receipt_dir / out
    else:
        out = receipt_dir / f"plan-{_timestamp_slug()}.json"
    out, payload = _write_plan(out, services, inventory)
    pointer_payload = {
        "generated_at": payload["generated_at"],
        "plan": _rel(out),
        "services": services,
    }
    _write_json(receipt_dir / "plan-latest.json", pointer_payload)
    print(f"plan written → {_rel(out)}")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    if not plan_path.exists():
        raise SystemExit(f"plan not found: {plan_path}")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    service_names = [svc["service"] for svc in plan.get("services", [])]
    receipt = plan_path.with_suffix(plan_path.suffix + ".apply.json")
    payload = {
        "plan": _rel(plan_path),
        "services": service_names,
        "dry_run": bool(args.dry_run),
        "applied_at": shared.utc_timestamp(),
        "status": "dry-run" if args.dry_run else "noop",
        "notes": "Implementation scaffolding only - refactors recorded manually.",
    }
    receipt.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.dry_run:
        print(f"[dry-run] would consolidate services: {', '.join(service_names)}")
    else:
        print(f"apply recorded (manual follow-up required) → {_rel(receipt)}")
    return 0


def _duplication_stats() -> Mapping[str, int]:
    counter: Counter[str] = Counter()
    for spec in SERVICE_SPEC.values():
        for module in spec["modules"]:
            path = ROOT / module
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            for token in PRIMITIVE_TOKENS:
                if token in text:
                    counter[token] += text.count(token)
    return dict(counter)


def cmd_telemetry(args: argparse.Namespace) -> int:
    receipt_dir = _ensure_receipt_dir(args.receipt_dir)
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = receipt_dir / out
        out.parent.mkdir(parents=True, exist_ok=True)
    else:
        out = receipt_dir / f"telemetry-{_timestamp_slug()}.json"
    start = time.perf_counter()
    inventory = _collect_inventory()
    duration_ms = (time.perf_counter() - start) * 1000
    payload = {
        "schema": "autonomy.module_consolidation.telemetry/v1",
        "generated_at": shared.utc_timestamp(),
        "inventory_duration_ms": round(duration_ms, 2),
        "services": [
            {
                "service": row["service"],
                "module_count": row["module_count"],
                "line_count": row["line_count"],
                "primitive_hits": row["primitive_hits"],
            }
            for row in inventory
        ],
        "duplication_tokens": _duplication_stats(),
    }
    _write_json(out, payload)
    pointer_payload = {
        "generated_at": payload["generated_at"],
        "telemetry": _rel(out),
    }
    _write_json(receipt_dir / "telemetry-latest.json", pointer_payload)
    print(f"telemetry written → {_rel(out)}")
    return 0


def cmd_guard(args: argparse.Namespace) -> int:
    receipt_dir = _ensure_receipt_dir(args.receipt_dir)
    errors: list[str] = []

    def _check_pointer(pointer_name: str, key: str) -> Path | None:
        pointer_path = receipt_dir / pointer_name
        if not pointer_path.exists():
            errors.append(f"missing {pointer_name} in {receipt_dir}")
            return None
        try:
            payload = json.loads(pointer_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid {pointer_name}: {exc}")
            return None
        path_str = payload.get(key)
        if not path_str:
            errors.append(f"{pointer_name} missing '{key}' field")
            return None
        target = _abs_path(path_str)
        if not target.exists():
            errors.append(f"{pointer_name} points to missing file: {path_str}")
            return None
        generated_at = payload.get("generated_at")
        parsed = _parse_ts(generated_at)
        if parsed is None:
            errors.append(f"{pointer_name} missing/invalid generated_at")
        else:
            age_hours = (datetime.now(timezone.utc) - parsed).total_seconds() / 3600.0
            if age_hours > args.max_age_hours:
                errors.append(
                    f"{pointer_name} older than {args.max_age_hours}h (generated {generated_at})"
                )
        return target

    plan_path = _check_pointer("plan-latest.json", "plan")
    telemetry_path = _check_pointer("telemetry-latest.json", "telemetry")

    if plan_path is not None:
        try:
            plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
            services = {svc["service"] for svc in plan_payload.get("services", []) if isinstance(svc, Mapping)}
        except json.JSONDecodeError as exc:
            errors.append(f"plan receipt invalid JSON: {plan_path}: {exc}")
            services = set()
    else:
        services = set()

    if telemetry_path is not None:
        try:
            telemetry_payload = json.loads(telemetry_path.read_text(encoding="utf-8"))
            telemetry_services = {svc["service"] for svc in telemetry_payload.get("services", []) if isinstance(svc, Mapping)}
        except json.JSONDecodeError as exc:
            errors.append(f"telemetry receipt invalid JSON: {telemetry_path}: {exc}")
            telemetry_services = set()
        if services and telemetry_services and services != telemetry_services:
            errors.append("plan/telemetry service sets differ")

    if errors:
        for message in errors:
            print(f"::error::{message}")
        return 1
    print("autonomy module consolidation receipts healthy")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory_cmd = subparsers.add_parser(
        "inventory",
        help="Summarise current autonomy modules vs target services",
    )
    inventory_cmd.add_argument("--format", choices=("table", "json"), default="table")
    inventory_cmd.set_defaults(func=cmd_inventory)

    plan_cmd = subparsers.add_parser("plan", help="Generate migration plan receipt")
    plan_cmd.add_argument("--service", action="append", help="Service(s) to include (default all)")
    plan_cmd.add_argument("--out", help="Output path (default: _report/usage/autonomy-module-consolidation/plan-<ts>.json)")
    plan_cmd.add_argument("--receipt-dir", help="Custom receipt directory")
    plan_cmd.set_defaults(func=cmd_plan)

    apply_cmd = subparsers.add_parser("apply", help="Record consolidation run (no-op placeholder)")
    apply_cmd.add_argument("--plan", required=True, help="Plan receipt to apply")
    apply_cmd.add_argument("--dry-run", action="store_true", help="Only record intent without writing state")
    apply_cmd.set_defaults(func=cmd_apply)

    telemetry_cmd = subparsers.add_parser("telemetry", help="Capture telemetry metrics + pointer")
    telemetry_cmd.add_argument("--out", help="Telemetry receipt path (default: _report/.../telemetry-<ts>.json)")
    telemetry_cmd.add_argument("--receipt-dir", help="Custom receipt directory")
    telemetry_cmd.set_defaults(func=cmd_telemetry)

    guard_cmd = subparsers.add_parser("guard", help="Validate consolidation receipts and freshness")
    guard_cmd.add_argument("--receipt-dir", help="Receipt directory (default: _report/usage/autonomy-module-consolidation)")
    guard_cmd.add_argument("--max-age-hours", type=float, default=24.0, help="Maximum allowed pointer age (hours, default 24)")
    guard_cmd.set_defaults(func=cmd_guard)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    func = getattr(args, "func", None)
    if not callable(func):
        parser.print_help()
        return 2
    return func(args)


if __name__ == "__main__":
    raise SystemExit(main())
