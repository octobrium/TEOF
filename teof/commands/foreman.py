from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from typing import Callable, Iterable

from . import brief as brief_cmd
from . import scan as scan_cmd
from . import status as status_cmd
from . import tasks as tasks_cmd


@dataclass(frozen=True)
class ForemanAction:
    name: str
    keywords: tuple[str, ...]
    runner: Callable[[], int]
    success: str


def _run_scan_summary() -> int:
    args = argparse.Namespace(
        limit=10,
        format="table",
        summary=True,
        out=None,
        emit_bus=False,
        emit_plan=False,
        only=None,
        skip=None,
    )
    print("Foreman ▸ Running alignment scan (summary)…")
    return scan_cmd.run(args)


def _run_status_snapshot() -> int:
    args = argparse.Namespace(out=None, quiet=False)
    print("Foreman ▸ Generating status snapshot…")
    return status_cmd.run(args)


def _run_tasks_table() -> int:
    args = argparse.Namespace(format="table", all=False)
    print("Foreman ▸ Listing active tasks…")
    return tasks_cmd.run(args)


def _run_brief() -> int:
    args = argparse.Namespace()
    print("Foreman ▸ Building brief scorer outputs…")
    return brief_cmd.run(args)


def _run_daily_cycle() -> int:
    print("Foreman ▸ Running daily alignment cycle (status → scan → tasks)…")
    status_code = _run_status_snapshot()
    if status_code != 0:
        print("Foreman ▸ Status snapshot failed; continuing to scan/tasks for visibility.")
    scan_code = _run_scan_summary()
    if scan_code != 0:
        print("Foreman ▸ Alignment scan reported issues; review output above.")
    tasks_code = _run_tasks_table()
    exit_code = max(status_code, scan_code, tasks_code)
    if exit_code == 0:
        print("Foreman ▸ Daily alignment cycle complete.")
    else:
        print(
            f"Foreman ▸ Daily cycle encountered issues "
            f"(status={status_code}, scan={scan_code}, tasks={tasks_code})."
        )
    return exit_code


def _run_help() -> int:
    print(
        "Foreman ▸ I can interpret plain requests like:\n"
        "  • \"run the alignment scan\"\n"
        "  • \"show me the status\"\n"
        "  • \"list today’s tasks\"\n"
        "  • \"rebuild the brief\"\n"
        "Pass text with `teof foreman --say \"…\"`, `teof foreman \"…\"`, or call without arguments to type interactively."
    )
    return 0


def _normalise(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned.lower()


def _spoken_from_args(args: argparse.Namespace) -> str | None:
    spoken = getattr(args, "say", None)
    if spoken is not None:
        cleaned = spoken.strip()
        return cleaned or None
    words = getattr(args, "phrase", None)
    if words:
        joined = " ".join(words).strip()
        return joined or None
    return None


_ACTIONS: tuple[ForemanAction, ...] = (
    ForemanAction("help", ("help", "what can you do"), _run_help, "Displayed helper prompts."),
    ForemanAction(
        "daily",
        ("daily", "routine", "cycle"),
        _run_daily_cycle,
        "Daily alignment cycle complete.",
    ),
    ForemanAction("scan", ("scan", "alignment", "check"), _run_scan_summary, "Alignment scan complete."),
    ForemanAction("status", ("status", "snapshot", "state"), _run_status_snapshot, "Status snapshot complete."),
    ForemanAction("tasks", ("task", "todo", "next"), _run_tasks_table, "Task summary complete."),
    ForemanAction("brief", ("brief", "score", "ensemble"), _run_brief, "Brief artifacts refreshed."),
)


def _choose_action(text: str, actions: Iterable[ForemanAction]) -> ForemanAction | None:
    normalised = _normalise(text)
    if not normalised:
        return None
    for action in actions:
        if any(keyword in normalised for keyword in action.keywords):
            return action
    return None


def run(args: argparse.Namespace) -> int:
    spoken = _spoken_from_args(args)
    if spoken is None:
        try:
            spoken = input("Foreman ▸ How can I help? ").strip()
        except EOFError:
            spoken = ""
    action = _choose_action(spoken or "", _ACTIONS)
    if action is None:
        print(
            "Foreman ▸ I could not map that request.\n"
            "Try phrases like \"run the scan\", \"show status\", or \"list tasks\"."
        )
        return 2
    code = action.runner()
    if code == 0:
        print(f"Foreman ▸ {action.success}")
    else:
        print(f"Foreman ▸ Command '{action.name}' exited with status {code}")
    return code


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "foreman",
        help="Interpret a natural-language request and route to the right TEOF command",
    )
    parser.add_argument(
        "--say",
        metavar="TEXT",
        help="Plain-language instruction (otherwise prompted interactively)",
    )
    parser.add_argument(
        "phrase",
        nargs=argparse.REMAINDER,
        help="Plain-language instruction (alternate to --say)",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run", "_choose_action", "_ACTIONS", "_spoken_from_args"]
