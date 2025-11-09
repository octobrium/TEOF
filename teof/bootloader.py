#!/usr/bin/env python3
"""Repo-local TEOF CLI bootstrapper.

Provides a minimal subset of the production CLI so tests can invoke
`teof brief` without requiring a separate installation while delegating
command logic to dedicated modules under ``teof.commands``.
"""
from __future__ import annotations

import argparse
import signal
from pathlib import Path
from typing import Iterable

from teof.commands import register_commands
from teof.commands import brief as cmd_brief_mod
from teof.commands import status as cmd_status_mod
from teof.commands import tasks as cmd_tasks_mod
from teof.commands import reflections as cmd_reflections_mod
from teof.commands import ttd_trend as cmd_ttd_trend_mod
from teof.commands import scan as cmd_scan_mod
from teof.commands import frontier as cmd_frontier_mod
from teof.commands import critic as cmd_critic_mod
from teof.commands import tms as cmd_tms_mod
from teof.commands import ethics as cmd_ethics_mod
from teof.commands import ideas as cmd_ideas_mod
from teof import reflections_report, status_report, tasks_report  # backward-compatible exports
from teof._paths import repo_root
from tools.autonomy import critic as critic_mod  # noqa: F401  (tests rely on these attributes)
from tools.autonomy import ethics_gate as ethics_mod  # noqa: F401
from tools.autonomy import frontier as frontier_mod  # noqa: F401
from tools.autonomy import tms as tms_mod  # noqa: F401
from tools.impact import ttd_trend as ttd_trend_mod  # noqa: F401


ROOT = repo_root(default=Path(__file__).resolve().parents[1])
SCAN_COMPONENTS = cmd_scan_mod.SCAN_COMPONENTS
_SIGPIPE_CONFIGURED = False


def _configure_sigpipe() -> None:
    global _SIGPIPE_CONFIGURED
    if _SIGPIPE_CONFIGURED:
        return
    try:
        sigpipe = signal.SIGPIPE
        sigdfl = signal.SIG_DFL
    except AttributeError:
        _SIGPIPE_CONFIGURED = True
        return
    try:
        signal.signal(sigpipe, sigdfl)
    except (OSError, ValueError):
        pass
    _SIGPIPE_CONFIGURED = True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="teof", description="TEOF CLI (repo-local subset)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    register_commands(subparsers)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    _configure_sigpipe()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    func = getattr(args, "func", None)
    if not callable(func):
        parser.print_help()
        return 2
    return func(args)


# Backward-compatible command entry points used by existing tests and tooling.
def cmd_brief(args: argparse.Namespace) -> int:
    return cmd_brief_mod.run(args)


def cmd_status(args: argparse.Namespace) -> int:
    return cmd_status_mod.run(args)


def cmd_tasks(args: argparse.Namespace) -> int:
    return cmd_tasks_mod.run(args)


def cmd_reflections(args: argparse.Namespace) -> int:
    return cmd_reflections_mod.run(args)


def cmd_ttd_trend(args: argparse.Namespace) -> int:
    return cmd_ttd_trend_mod.run(args)


def cmd_scan(args: argparse.Namespace) -> int:
    return cmd_scan_mod.run(args)


def cmd_frontier(args: argparse.Namespace) -> int:
    return cmd_frontier_mod.run(args)


def cmd_critic(args: argparse.Namespace) -> int:
    return cmd_critic_mod.run(args)


def cmd_tms(args: argparse.Namespace) -> int:
    return cmd_tms_mod.run(args)


def cmd_ethics(args: argparse.Namespace) -> int:
    return cmd_ethics_mod.run(args)


def cmd_ideas(args: argparse.Namespace) -> int:
    return cmd_ideas_mod.run(args)


if __name__ == "__main__":
    import sys

    sys.exit(main())
