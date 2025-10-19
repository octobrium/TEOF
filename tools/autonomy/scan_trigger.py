"""Reactive alignment scan trigger.

Run the scan driver only when tracked paths (plans, receipts, etc.)
change. Designed for git hooks or lightweight automation so we avoid
blind scheduling loops.
"""
from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from teof import bootloader


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WATCH = ("_plans/", "_report/")


def _git_status_paths(root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return []
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        # Format: XY <path> (we ignore status codes)
        path = line[3:].strip()
        if path:
            paths.append(path)
    return paths


def _should_trigger(changed: Iterable[str], watch: Sequence[str]) -> bool:
    prefixes = tuple(watch)
    for path in changed:
        normalised = path.replace("\\", "/")
        if normalised.startswith(prefixes):
            return True
    return False


@dataclass(frozen=True)
class TriggerReport:
    changed_paths: list[str]
    triggered: bool
    watch_prefixes: tuple[str, ...]


def evaluate_trigger(*, root: Path, watch: Sequence[str]) -> TriggerReport:
    changed = _git_status_paths(root)
    triggered = _should_trigger(changed, watch)
    return TriggerReport(changed_paths=changed, triggered=triggered, watch_prefixes=tuple(watch))


def run_scan(summary: bool = True) -> int:
    argv: list[str] = ["scan"]
    if summary:
        argv.append("--summary")
    return bootloader.main(argv)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--watch",
        action="append",
        dest="watch",
        help="Relative path prefix to monitor (repeatable). Defaults to _plans/ and _report/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report whether a trigger would run (no scan execution)",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Run full scan output instead of summary mode",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    watch = tuple(args.watch) if args.watch else DEFAULT_WATCH
    report = evaluate_trigger(root=ROOT, watch=watch)
    if not report.changed_paths:
        print("scan_trigger: no git changes detected")
    else:
        print(
            f"scan_trigger: detected {len(report.changed_paths)} changed path(s); "
            f"watching prefixes {report.watch_prefixes}"
        )
    if not report.triggered:
        print("scan_trigger: no watched paths changed; skipping scan")
        return 0
    if args.dry_run:
        print("scan_trigger: dry-run enabled; would run teof scan")
        return 0
    summary = not args.no_summary
    exit_code = run_scan(summary=summary)
    if exit_code == 0:
        print("scan_trigger: scan completed")
    else:
        print(f"scan_trigger: scan exited with status {exit_code}")
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
