from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from teof._paths import repo_root
from tools.autonomy.bus_guard import BusGuard, BusIssue


def _issue_payload(issue: BusIssue) -> dict[str, object]:
    payload = asdict(issue)
    return payload


def _render_text(issues: list[BusIssue]) -> str:
    if not issues:
        return "Bus guard: no issues detected"
    lines = [f"Bus guard: {len(issues)} issue(s)"]
    for issue in issues:
        location = issue.path
        if issue.line is not None:
            location = f"{location}:L{issue.line}"
        status = "fixed" if issue.fixed else "needs attention"
        lines.append(f"- [{status}] {location} — {issue.message}")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> int:
    root = repo_root()
    guard = BusGuard(root)
    issues = guard.run(autofix=getattr(args, "fix", False))
    fmt = getattr(args, "format", "text").lower()
    if fmt == "json":
        payload = {
            "root": str(root),
            "fix_applied": bool(getattr(args, "fix", False)),
            "issue_count": len(issues),
            "issues": [_issue_payload(issue) for issue in issues],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text(issues))
    outstanding = any(not issue.fixed for issue in issues)
    return 0 if not outstanding else 2


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser("bus_guard", help="Validate and optionally repair bus artifacts")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt safe repairs (status, timestamps, defaults) for common issues",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
