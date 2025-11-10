#!/usr/bin/env python3
"""Evaluate whether an agent session is ready to push to main."""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

from tools.planner import evidence_scope as planner_evidence
from tools.planner import validate as planner_validate

ROOT = Path(__file__).resolve().parents[2]
CLAIMS_DIR = ROOT / "_bus" / "claims"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"
TERMINAL_CLAIM_STATUSES = {"done", "released", "closed", "cancelled", "abandoned"}
OPTIONAL_RECEIPT_PREFIXES = planner_validate.RECEIPT_TRACKING_OPTIONAL_PREFIXES


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: Optional[str] = None


def _run_git(args: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _manifest_agent() -> Optional[str]:
    if not MANIFEST_PATH.exists():
        return None
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    agent = data.get("agent_id")
    if isinstance(agent, str) and agent.strip():
        return agent.strip()
    return None


def check_clean_worktree() -> CheckResult:
    dirty = _run_git(["status", "--porcelain"])
    ok = dirty.strip() == ""
    return CheckResult("git_clean", ok, None if ok else "working tree has staged or unstaged changes")


def _current_branch() -> str:
    return _run_git(["rev-parse", "--abbrev-ref", "HEAD"])


def check_branch(agent: str, allowed: Set[str]) -> CheckResult:
    branch = _current_branch()
    ok = branch == "main" or branch.startswith(f"agent/{agent}/") or branch in allowed
    details = None if ok else f"branch '{branch}' not allowed (expect main or agent/{agent}/*)"
    return CheckResult("branch_match", ok, details)


def _iter_claims() -> Iterable[Path]:
    if not CLAIMS_DIR.exists():
        return []
    return CLAIMS_DIR.glob("*.json")


def check_claims(agent: str) -> CheckResult:
    active: List[str] = []
    for path in _iter_claims():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("agent_id") != agent:
            continue
        status = str(data.get("status", "")).lower()
        if status not in TERMINAL_CLAIM_STATUSES:
            active.append(path.name)
    ok = not active
    return CheckResult("claims_clear", ok, None if ok else f"active claims present: {', '.join(sorted(active))}")


def _rel_to_root(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _tracking_required(rel: str) -> bool:
    return not any(rel.startswith(prefix) for prefix in OPTIONAL_RECEIPT_PREFIXES)


def _is_tracked(path: Path) -> bool:
    rel = _rel_to_root(path)
    if not _tracking_required(rel):
        return True
    return bool(_run_git(["ls-files", rel]))


def check_paths(name: str, paths: Iterable[Path]) -> CheckResult:
    missing: List[str] = []
    for path in paths:
        rel = _rel_to_root(path)
        if not path.exists():
            missing.append(f"{rel} (missing)")
        elif not _is_tracked(path):
            missing.append(f"{rel} (untracked)")
    ok = not missing
    return CheckResult(name, ok, None if ok else ", ".join(missing))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check whether the session is ready to push to main")
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json)")
    parser.add_argument("--allow-branch", action="append", default=[], help="Extra branch names allowed in addition to main and agent/<id>/ prefix")
    parser.add_argument("--require-receipt", action="append", default=[], help="Receipt path that must exist and be tracked")
    parser.add_argument("--require-test", action="append", default=[], help="Test receipt path that must exist and be tracked")
    parser.add_argument(
        "--require-evidence-plan",
        action="append",
        default=[],
        help="Plan id that must satisfy the evidence_scope guard (repeatable)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    agent = args.agent or _manifest_agent()
    if not agent:
        parser.error("Agent id not provided and AGENT_MANIFEST.json missing")

    results = [
        check_clean_worktree(),
        check_branch(agent, set(args.allow_branch)),
        check_claims(agent),
    ]

    if args.require_receipt:
        results.append(check_paths("receipts_exist", [ROOT / Path(p) for p in args.require_receipt]))
    if args.require_test:
        results.append(check_paths("tests_exist", [ROOT / Path(p) for p in args.require_test]))
    if args.require_evidence_plan:
        ok, reports = planner_evidence.require_evidence(args.require_evidence_plan, strict=True)
        if reports:
            if ok:
                detail = "; ".join(
                    f"{report.plan_id}: internal={report.counts['internal']}, "
                    f"external={report.counts['external']}, comparative={report.counts['comparative']}, "
                    f"receipts={len(report.receipts)}"
                    for report in reports
                )
            else:
                detail = "; ".join(
                    f"{report.plan_id}: {', '.join(report.errors) or 'missing evidence'}"
                    for report in reports
                )
        else:
            detail = "no plan ids supplied"
        results.append(CheckResult("evidence_scope", ok, detail))

    ready = all(r.ok for r in results)
    payload = {
        "agent": agent,
        "branch": _current_branch(),
        "ready": ready,
        "checks": [
            {"name": r.name, "ok": r.ok, **({"details": r.details} if r.details else {})}
            for r in results
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
