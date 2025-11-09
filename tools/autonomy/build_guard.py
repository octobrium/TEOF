#!/usr/bin/env python3
"""Guard to ensure build artifacts are not tracked in git."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("dist/**", "Python distribution artifacts under dist/"),
    ("build/**", "Build outputs under build/"),
    ("*.egg-info/**", "Setuptools egg metadata"),
    ("artifacts/systemic_out/**", "Systemic brief outputs (should remain untracked)"),
)


@dataclass(frozen=True)
class Match:
    pattern: str
    reason: str
    paths: Sequence[str]


def _git_ls_files(root: Path, pattern: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--", pattern],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git ls-files failed for {pattern!r}: {message}")
    return [line for line in result.stdout.splitlines() if line.strip()]


def detect_tracked_artifacts(
    root: Path,
    *,
    allow: Iterable[str] | None = None,
    patterns: Iterable[tuple[str, str]] = DEFAULT_PATTERNS,
) -> list[Match]:
    root = root.resolve()
    allow_set = {entry.strip() for entry in (allow or []) if entry and entry.strip()}
    matches: list[Match] = []
    for pattern, reason in patterns:
        if pattern in allow_set:
            continue
        paths = _git_ls_files(root, pattern)
        if paths:
            matches.append(Match(pattern=pattern, reason=reason, paths=tuple(paths)))
    return matches


def _print_text(matches: Sequence[Match]) -> None:
    if matches:
        print("build_guard: tracked build artifacts detected:")
        for match in matches:
            print(f"- pattern: {match.pattern} ({match.reason})")
            for path in match.paths:
                print(f"  * {path}")
    else:
        print("build_guard: no tracked build artifacts found")


def _print_json(matches: Sequence[Match]) -> None:
    payload = {
        "status": "fail" if matches else "ok",
        "matches": [
            {"pattern": match.pattern, "reason": match.reason, "paths": list(match.paths)}
            for match in matches
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect tracked build artifacts.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root (default: cwd)")
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        help="Patterns to ignore (repeatable, must match a default pattern exactly)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    matches = detect_tracked_artifacts(args.root, allow=args.allow)
    if args.format == "json":
        _print_json(matches)
    else:
        _print_text(matches)
    return 1 if matches else 0


if __name__ == "__main__":
    raise SystemExit(main())
