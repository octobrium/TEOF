from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATTERN = re.compile(r"_plans/([0-9][^/]+)\.plan\.json")
REPORT_PATTERN = re.compile(r"_report/(?:agent|manager)/[^/]+/([0-9][^/]+)/")
DEFAULT_FILE_THRESHOLD = 50
DEFAULT_PLAN_THRESHOLD = 2


@dataclass
class DeadlockSignal:
    dirty_files: int
    plan_ids: list[str]
    suspected: bool
    reasons: list[str]


def _git_status(root: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git status failed")
    return result.stdout


def _parse_plan_ids(paths: Iterable[str]) -> list[str]:
    plan_ids: set[str] = set()
    for path in paths:
        match = PLAN_PATTERN.search(path)
        if match:
            plan_ids.add(match.group(1))
            continue
        match = REPORT_PATTERN.search(path)
        if match:
            plan_ids.add(match.group(1))
    return sorted(plan_ids)


def detect_deadlock(
    *,
    root: Path,
    file_threshold: int,
    plan_threshold: int,
) -> DeadlockSignal:
    status_text = _git_status(root)
    dirty_paths = [line[3:] for line in status_text.splitlines() if len(line) > 3]
    plan_ids = _parse_plan_ids(dirty_paths)

    reasons: list[str] = []
    suspected = False
    if len(dirty_paths) >= file_threshold:
        reasons.append(f"{len(dirty_paths)} dirty files (threshold {file_threshold})")
        suspected = True
    if len(plan_ids) >= plan_threshold:
        reasons.append(f"{len(plan_ids)} plans touched: {', '.join(plan_ids)}")
        suspected = True
    return DeadlockSignal(len(dirty_paths), plan_ids, suspected, reasons)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _summary(signal: DeadlockSignal) -> str:
    lines = [
        f"Coordination status: {'POTENTIAL DEADLOCK' if signal.suspected else 'clear'}",
        f"Dirty files: {signal.dirty_files}",
        f"Plans touched: {', '.join(signal.plan_ids) if signal.plan_ids else '(none)'}",
    ]
    if signal.reasons:
        lines.append("Triggers:")
        lines.extend(f"  - {reason}" for reason in signal.reasons)
        lines.append("Recommended: run `teof plan_scope --plan <id>` per plan, consider `git worktree` for isolation, and follow docs/workflow.md deadlock protocol.")
    else:
        lines.append("Recommended: keep using `teof plan_scope` to scope pushes.")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> int:
    try:
        signal = detect_deadlock(
            root=ROOT,
            file_threshold=args.file_threshold,
            plan_threshold=args.plan_threshold,
        )
    except Exception as exc:  # pragma: no cover - surfaced to operator
        print(f"teof deadlock: unable to assess repository state: {exc}", file=sys.stderr)
        return 2

    payload = {
        "generated_at": _timestamp(),
        "dirty_files": signal.dirty_files,
        "plans_touched": signal.plan_ids,
        "suspected_deadlock": signal.suspected,
        "reasons": signal.reasons,
        "recommendations": [
            "Run `teof plan_scope --plan <id>` for each plan before pushing.",
            "Use `git worktree add` to isolate concurrent plans.",
            "Follow docs/workflow.md deadlock protocol if recursion persists.",
        ],
    }

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_summary(signal))

    return 1 if signal.suspected else 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "deadlock",
        help="Detect potential coordination deadlocks (guard recursion / multi-plan worktrees)",
    )
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    parser.add_argument(
        "--file-threshold",
        type=int,
        default=DEFAULT_FILE_THRESHOLD,
        help="Dirty file count that triggers a deadlock warning (default: 50)",
    )
    parser.add_argument(
        "--plan-threshold",
        type=int,
        default=DEFAULT_PLAN_THRESHOLD,
        help="Number of simultaneous plans that triggers a deadlock warning (default: 2)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
