"""Automate the Tier 1 onboarding loop with receipts."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from teof._paths import repo_root
from teof.commands import up as up_cmd
from tools.agent import session_boot, session_guard
from tools.autonomy.shared import atomic_write_json

ROOT = repo_root(default=Path(__file__).resolve().parents[2])
AUTOMATION_RECEIPT_DIR = ROOT / "_report" / "usage" / "onboarding" / "automation"
SESSION_DIR = ROOT / "_report" / "session"

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _git_rev() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        return proc.stdout.strip()
    except Exception:
        return "unknown"


def _run_syscheck(min_version: tuple[int, int] = (3, 9)) -> Dict[str, Any]:
    issues: list[str] = []
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    if (version_info.major, version_info.minor) < min_version:
        issues.append(
            f"Python {min_version[0]}.{min_version[1]}+ required (found {version_str})"
        )

    python_cli = shutil.which("python3")
    if python_cli is None:
        issues.append("python3 executable not found on PATH")

    try:
        pip_proc = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        pip_path = pip_proc.stdout.strip()
    except Exception:
        pip_path = None
        issues.append("pip inaccessible via 'python3 -m pip --version'")

    pytest_path = shutil.which("pytest")
    if pytest_path is None:
        issues.append("pytest not found on PATH")

    return {
        "python_version": version_str,
        "python_path": python_cli or sys.executable,
        "pip_path": pip_path,
        "pytest_path": pytest_path,
        "issues": issues,
    }


def _run_teof_eval(skip_install: bool) -> up_cmd.Tier1Result:
    runner = up_cmd.WORKLOADS["tier1-eval"]
    return runner(skip_install, up_cmd.ONBOARDING_REPORT_DIR)


def _session_tail(agent_id: str) -> str | None:
    tail = SESSION_DIR / agent_id / "manager-report-tail.txt"
    return _rel(tail) if tail.exists() else None


def _ensure_session(agent_id: str, focus: str | None) -> None:
    argv = ["--agent", agent_id, "--with-status"]
    if focus:
        argv.extend(["--focus", focus])
    session_boot.main(argv)


def _write_receipt(
    agent_id: str,
    focus: str | None,
    syscheck: Dict[str, Any],
    tier1: up_cmd.Tier1Result,
    *,
    receipt_dir: Path | None = None,
) -> Path:
    receipt_dir = receipt_dir or AUTOMATION_RECEIPT_DIR
    receipt_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _iso_now()
    run_id = f"{timestamp.replace(':', '').replace('-', '')}-onboarding-automation"
    payload: Dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": run_id,
        "generated_at": timestamp,
        "agent_id": agent_id,
        "focus": focus or "autonomy",
        "git_revision": _git_rev(),
        "syscheck": syscheck,
        "commands": [
            "tools.agent.session_boot",
            "teof.syscheck",
            "teof.up.tier1-eval",
        ],
        "session": {
            "manager_report_tail": _session_tail(agent_id),
        },
        "tier1_eval": {
            "artifact_dir": _rel(tier1["artifact_dir"]),
            "document_count": tier1["document_count"],
            "score": tier1["score_text"],
            "ensembles": [f"{_rel(tier1['artifact_dir'])}/{name}" for name in tier1["ensembles"]],
            "metadata": _rel(tier1["metadata_path"]),
            "eval_receipt": _rel(tier1["eval_receipt"]),
            "quickstart_receipt": _rel(tier1["quickstart_receipt"])
            if tier1["quickstart_receipt"]
            else None,
            "quickstart_git": tier1.get("quickstart_git"),
            "quickstart_intent": tier1.get("quickstart_intent"),
        },
    }
    receipt_path = receipt_dir / f"{run_id}.json"
    atomic_write_json(receipt_path, payload)

    latest = receipt_dir / "latest.json"
    try:
        if latest.is_symlink() or latest.exists():
            latest.unlink()
        latest.symlink_to(receipt_path.name)
    except OSError:
        atomic_write_json(latest, {"latest": receipt_path.name})
    return receipt_path


def run(args: argparse.Namespace) -> int:
    agent_id = session_guard.resolve_agent_id(getattr(args, "agent", None))
    focus = getattr(args, "focus", None)
    if not getattr(args, "skip_session", False):
        _ensure_session(agent_id, focus)

    syscheck = _run_syscheck()
    if syscheck["issues"]:
        raise SystemExit(
            "syscheck failed:\n" + "\n".join(f"- {issue}" for issue in syscheck["issues"])
        )

    tier1 = _run_teof_eval(bool(getattr(args, "skip_install", False)))
    receipt_path = _write_receipt(agent_id, focus, syscheck, tier1, receipt_dir=AUTOMATION_RECEIPT_DIR)
    print(f"Onboarding automation complete → {_rel(receipt_path)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.autonomy.onboarding_runner",
        description="Automate the Tier 1 onboarding loop (syscheck + teof up) with receipts.",
    )
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST).")
    parser.add_argument("--focus", help="Focus string passed to session_boot.", default="autonomy")
    parser.add_argument(
        "--skip-session",
        action="store_true",
        help="Skip running session_boot (expects an existing fresh session).",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip pip install during Tier 1 evaluation (for pre-installed envs).",
    )
    parser.set_defaults(func=run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
