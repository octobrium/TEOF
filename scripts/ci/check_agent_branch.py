#!/usr/bin/env python3
"""CI guard for agent/* branches."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _git_diff(base: str) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"::error::failed to compute diff vs {base}: {exc}", file=sys.stderr)
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    branch = (
        os.environ.get("GITHUB_HEAD_REF")
        or os.environ.get("PR_HEAD_REF")
        or os.environ.get("GITHUB_REF_NAME")
        or ""
    )
    if not branch.startswith("agent/"):
        print("::notice::non-agent branch; skipping agent checks")
        return 0

    base_sha = os.environ.get("BASE_SHA") or os.environ.get("PR_BASE_SHA")
    if not base_sha:
        try:
            base_sha = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], text=True).strip()
        except subprocess.CalledProcessError:
            base_sha = "HEAD^"

    changed = _git_diff(base_sha)
    plan_changes = [p for p in changed if p.startswith("_plans/") and p.endswith(".plan.json")]
    md_changes = [p for p in changed if p.startswith("_plans/") and p.endswith(".md")]

    errors: list[str] = []
    if not plan_changes:
        errors.append("agent branches must change at least one plan file under _plans/*.plan.json")
    if not md_changes:
        errors.append("agent branches must include a justification Markdown file under _plans/")

    manifest_path = Path("AGENT_MANIFEST.json")
    if not manifest_path.exists():
        errors.append("AGENT_MANIFEST.json missing; copy AGENT_MANIFEST.example.json and fill it in")

    if errors:
        for err in errors:
            print(f"::error::{err}", file=sys.stderr)
        if changed:
            print("Files changed:", file=sys.stderr)
            for path in changed:
                print(f"  - {path}", file=sys.stderr)
        return 1

    print("::notice::agent branch requirements satisfied", file=sys.stderr)
    for entry in plan_changes:
        print(f"::notice::plan touched {entry}", file=sys.stderr)
    for entry in md_changes:
        print(f"::notice::justification touched {entry}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
