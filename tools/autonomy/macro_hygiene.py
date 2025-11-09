"""Evaluate macro hygiene objectives and emit status receipts."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.autonomy.shared import load_json, write_receipt_payload

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "docs" / "maintenance" / "macro-hygiene.objectives.json"
DEFAULT_RECEIPT = ROOT / "_report" / "usage" / "macro-hygiene-status.json"

_PLAN_DONE_STATES = {"done", "completed", "satisfied"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


class MacroHygieneError(RuntimeError):
    """Raised when the macro hygiene ledger is missing or malformed."""


@dataclass
class CheckResult:
    kind: str
    target: str
    ok: bool
    detail: str
    optional: bool


def _load_config(path: Path) -> Mapping[str, Any]:
    data = load_json(path)
    if not isinstance(data, Mapping):
        raise MacroHygieneError(f"macro hygiene config missing or invalid: {path}")
    if "objectives" not in data:
        raise MacroHygieneError(f"macro hygiene config missing 'objectives': {path}")
    return data


def _check_plan_done(root: Path, rel_path: str, *, optional: bool) -> CheckResult:
    path = root / rel_path
    if not path.exists():
        return CheckResult("plan_done", rel_path, False, "plan file missing", optional)
    data = load_json(path)
    if not isinstance(data, Mapping):
        return CheckResult("plan_done", rel_path, False, "plan file unreadable", optional)
    status = str(data.get("status") or data.get("stage") or "").lower()
    ok = status in _PLAN_DONE_STATES
    detail = f"status={status or 'unknown'}"
    return CheckResult("plan_done", rel_path, ok, detail, optional)


def _check_path_exists(root: Path, rel_path: str, *, optional: bool) -> CheckResult:
    path = root / rel_path
    ok = path.exists()
    detail = "exists" if ok else "missing"
    if ok and path.is_file():
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            detail = f"exists (mtime={mtime.isoformat()})"
        except OSError:
            detail = "exists (mtime=unknown)"
    return CheckResult("path_exists", rel_path, ok, detail, optional)


def _evaluate_checks(root: Path, checks: Sequence[Mapping[str, Any]]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for index, check in enumerate(checks, 1):
        if not isinstance(check, Mapping):
            results.append(CheckResult("unknown", f"#{index}", False, "invalid check entry", False))
            continue
        kind = str(check.get("kind") or "").lower()
        target = str(check.get("path") or "")
        optional = bool(check.get("optional"))
        if not target:
            results.append(CheckResult(kind or "unknown", "?", False, "missing path", optional))
            continue
        if kind == "plan_done":
            results.append(_check_plan_done(root, target, optional=optional))
        elif kind == "path_exists":
            results.append(_check_path_exists(root, target, optional=optional))
        else:
            detail = "unsupported check kind"
            results.append(CheckResult(kind or "unknown", target, False, detail, optional))
    return results


def _objective_status(results: Iterable[CheckResult]) -> str:
    return "ready" if all(result.ok or result.optional for result in results) else "attention"


def compute_status(*, root: Path | None = None) -> Mapping[str, Any]:
    root = root or ROOT
    config = _load_config(CONFIG_PATH)
    objectives_raw = config.get("objectives")
    objectives: Sequence[Mapping[str, Any]] = (
        [obj for obj in objectives_raw if isinstance(obj, Mapping)] if isinstance(objectives_raw, Sequence) else []
    )

    evaluated: list[Mapping[str, Any]] = []
    ready = 0
    attention = 0

    for entry in objectives:
        identifier = str(entry.get("id") or "")
        checks_raw = entry.get("checks")
        checks = checks_raw if isinstance(checks_raw, Sequence) else []
        results = _evaluate_checks(root, checks)
        status = _objective_status(results)
        if status == "ready":
            ready += 1
        else:
            attention += 1
        evaluated.append(
            {
                "id": identifier,
                "title": entry.get("title"),
                "description": entry.get("description"),
                "owners": entry.get("owners"),
                "cadence": entry.get("cadence"),
                "status": status,
                "checks": [
                    {
                        "kind": result.kind,
                        "path": result.target,
                        "ok": result.ok,
                        "detail": result.detail,
                        "optional": result.optional,
                    }
                    for result in results
                ],
                "optional_failures": [
                    {
                        "kind": result.kind,
                        "path": result.target,
                        "detail": result.detail,
                    }
                    for result in results
                    if not result.ok and result.optional
                ],
                "signals": entry.get("signals"),
            }
        )

    overall = "ready" if attention == 0 else "attention"
    return {
        "generated_at": _iso_now(),
        "objectives": evaluated,
        "summary": {
            "ready": ready,
            "attention": attention,
            "total": len(evaluated),
        },
        "status": overall,
    }


def _print_human(status: Mapping[str, Any]) -> None:
    summary = status.get("summary") or {}
    print("Macro hygiene objectives")
    print(f"  Status: {status.get('status')} (ready={summary.get('ready')} attention={summary.get('attention')})")
    for objective in status.get("objectives") or []:
        title = objective.get("title") or objective.get("id")
        print(f"- {title}: {objective.get('status')}")
        for check in objective.get("checks") or []:
            prefix = "    ✓" if check.get("ok") or check.get("optional") else "    ×"
            opt = " (optional)" if check.get("optional") else ""
            print(f"{prefix} {check.get('kind')} {check.get('path')}{opt}: {check.get('detail')}")


def configure_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--no-write", action="store_true", help="Skip writing the receipt to disk")
    parser.add_argument("--out", type=Path, help=f"Custom output path (default: {DEFAULT_RECEIPT.relative_to(ROOT)})")
    parser.add_argument("--human", action="store_true", help="Print human-readable summary")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat optional checks as required (useful for debugging the ledger)",
    )
    return parser


def run_with_namespace(args: argparse.Namespace) -> int:
    status = compute_status()

    output = status
    if args.strict:
        output = json.loads(json.dumps(status))
        ready = 0
        attention = 0
        for objective in output.get("objectives", []):
            checks = objective.get("checks") or []
            if all(check.get("ok") for check in checks):
                objective["status"] = "ready"
                ready += 1
            else:
                objective["status"] = "attention"
                attention += 1
        summary = output.get("summary") or {}
        summary["ready"] = ready
        summary["attention"] = attention
        summary["total"] = ready + attention
        output["summary"] = summary
        output["status"] = "ready" if attention == 0 else "attention"
    if args.human:
        _print_human(output)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

    if not args.no_write:
        target = args.out if args.out else DEFAULT_RECEIPT
        if not target.is_absolute():
            target = ROOT / target
        write_receipt_payload(target, output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    return configure_parser(parser)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_with_namespace(args)


__all__ = ["compute_status", "main", "configure_parser", "run_with_namespace"]


if __name__ == "__main__":
    raise SystemExit(main())
