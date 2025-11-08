from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from teof._paths import repo_root
from tools.agent import session_guard
from tools.maintenance import repo_anatomy


REQUIRED_PATHS: tuple[str, ...] = (
    "_bus",
    "_plans",
    "_report",
    "docs",
    "tools",
    "tests",
    "teof",
    "memory",
)


@dataclass
class CheckResult:
    name: str
    status: str
    receipt: str | None = None
    details: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"name": self.name, "status": self.status}
        if self.receipt:
            payload["receipt"] = self.receipt
        if self.details:
            payload["details"] = self.details
        return payload


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _structure_check(*, root: Path, stamp: str, receipt_dir: Path) -> CheckResult:
    missing = [slug for slug in REQUIRED_PATHS if not (root / slug).exists()]
    stats = repo_anatomy.collect_stats(repo_anatomy.DEFAULT_PATHS)
    payload = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "required_paths": REQUIRED_PATHS,
        "missing_paths": missing,
        "paths": stats,
    }
    receipt_path = receipt_dir / f"structure-{stamp}.json"
    _write_json(receipt_path, payload)
    status = "ok" if not missing else "fail"
    details: dict[str, object] = {"missing_paths": missing, "checked": len(stats)}
    return CheckResult(
        name="structure",
        status=status,
        receipt=_relative(receipt_path, root),
        details=details,
    )


def _run_planner_validate(root: Path, summary_path: Path) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable or "python3",
        str(root / "tools" / "planner" / "validate.py"),
        "--strict",
        "--output",
        _relative(summary_path, root),
    ]
    return subprocess.run(cmd, cwd=root, check=False, text=True)


def _plan_validation_check(*, root: Path, stamp: str, receipt_dir: Path) -> CheckResult:
    summary_path = receipt_dir / f"plan-validate-{stamp}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    result = _run_planner_validate(root, summary_path)
    status = "ok" if result.returncode == 0 and summary_path.exists() else "fail"
    details: dict[str, object] = {"returncode": result.returncode}
    if not summary_path.exists():
        details["error"] = "plan validator did not emit summary"
    return CheckResult(
        name="plan_validation",
        status=status,
        receipt=_relative(summary_path, root) if summary_path.exists() else None,
        details=details,
    )


def _session_check(agent_id: str, *, root: Path) -> CheckResult:
    receipt = root / "_report" / "session" / agent_id / "manager-report-tail.txt"
    status = "ok" if receipt.exists() else "fail"
    details: dict[str, object] = {"agent_id": agent_id}
    if status != "ok":
        details["error"] = "manager-report tail missing"
    return CheckResult(
        name="session_receipt",
        status=status,
        receipt=_relative(receipt, root) if receipt.exists() else None,
        details=details,
    )


def build_parser(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser("operator", help="Operator utilities")
    operator_sub = parser.add_subparsers(dest="operator_command", required=True)

    verify = operator_sub.add_parser("verify", help="Run operator pre-flight checks")
    verify.add_argument("--agent", help="Agent id (defaults to manifest)")
    verify.add_argument(
        "--allow-stale-session",
        action="store_true",
        help="Allow stale session receipts (records override event)",
    )
    verify.add_argument(
        "--session-max-age",
        type=int,
        help="Override session freshness limit in seconds",
    )
    verify.add_argument(
        "--output",
        type=Path,
        help="Optional path for the operator verify receipt",
    )
    verify.add_argument(
        "--strict-plan",
        action="store_true",
        help="Include strict plan validation (operational tier)",
    )
    verify.set_defaults(func=_cmd_verify)


def register(subparsers: "argparse._SubParsersAction[object]") -> None:  # pragma: no cover - thin wrapper
    build_parser(subparsers)


def _cmd_verify(args: argparse.Namespace) -> int:
    root = repo_root()
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    receipt_dir = root / "_report" / "operator" / "verify"
    receipt_dir.mkdir(parents=True, exist_ok=True)

    agent_id = session_guard.resolve_agent_id(args.agent)
    session_guard.ensure_recent_session(
        agent_id,
        allow_stale=getattr(args, "allow_stale_session", False),
        max_age_seconds=getattr(args, "session_max_age", None),
        context="operator_verify",
    )

    checks: list[CheckResult] = []
    checks.append(_session_check(agent_id, root=root))
    checks.append(_structure_check(root=root, stamp=stamp, receipt_dir=receipt_dir))
    if getattr(args, "strict_plan", False):
        checks.append(_plan_validation_check(root=root, stamp=stamp, receipt_dir=receipt_dir))

    overall_ok = all(check.status == "ok" for check in checks)

    summary = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent_id": agent_id,
        "checks": [check.to_dict() for check in checks],
        "status": "ok" if overall_ok else "fail",
    }

    summary_path = Path(args.output) if args.output else (receipt_dir / f"operator-verify-{stamp}.json")
    if not summary_path.is_absolute():
        summary_path = root / summary_path
    _write_json(summary_path, summary)
    print(f"operator verify receipt → {_relative(summary_path, root)}")

    return 0 if overall_ok else 2
