from __future__ import annotations

import json
from datetime import datetime, timezone
from argparse import Namespace
from pathlib import Path
from typing import Iterable

from ._utils import DEFAULT_ROOT, relpath
from teof.ideas import (
    IDEA_DIR,
    VALID_STATUSES,
    Idea,
    iter_ideas,
    load_idea,
    resolve_idea,
    set_status,
    evaluate_ideas,
    write_idea,
)


def _ensure_status(raw: str) -> str:
    normalized = raw.strip().lower()
    if normalized not in VALID_STATUSES:
        raise SystemExit(f"--status must be one of {', '.join(VALID_STATUSES)}")
    return normalized


def _normalize_layers(layers: Iterable[str] | None) -> list[str]:
    if not layers:
        return []
    results: list[str] = []
    for entry in layers:
        token = entry.strip().upper()
        if token and token not in results:
            results.append(token)
    return results


def _normalize_systemic(values: Iterable[str] | None) -> list[int]:
    if not values:
        return []
    results: list[int] = []
    for entry in values:
        token = entry.strip()
        if not token:
            continue
        try:
            value = int(token)
        except ValueError:
            raise SystemExit(f"systemic scale must be integers (got {entry!r})") from None
        if value < 1 or value > 10:
            raise SystemExit("--systemic must be within 1..10")
        if value not in results:
            results.append(value)
    return results


def _load_and_update(path: Path, *, status: str | None, layers: list[str], systemic: list[int], plan_id: str | None) -> Idea:
    idea = load_idea(path)
    meta = dict(idea.meta)

    if status is not None:
        idea = set_status(idea, status)
        meta = dict(idea.meta)

    if layers:
        meta["layers"] = layers
    if systemic:
        meta["systemic"] = systemic
    if plan_id:
        meta["plan_id"] = plan_id

    idea.meta = meta
    return idea


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cmd_list(args: Namespace) -> int:
    ideas = iter_ideas()
    if args.directory:
        directory = Path(args.directory)
        ideas = iter_ideas(directory)

    statuses = {_ensure_status(status) for status in args.status} if args.status else None
    if statuses:
        ideas = [idea for idea in ideas if idea.status in statuses]

    if args.format == "json":
        payload = [
            {
                "id": idea.id,
                "title": idea.title,
                "status": idea.status,
                "path": relpath(idea.path, DEFAULT_ROOT),
                "created": idea.meta.get("created"),
                "updated": idea.meta.get("updated"),
                "layers": idea.meta.get("layers"),
                "systemic": idea.meta.get("systemic"),
                "plan_id": idea.meta.get("plan_id"),
            }
            for idea in ideas
        ]
        print(json.dumps({"ideas": payload, "count": len(payload)}, ensure_ascii=False, indent=2))
        return 0

    headers = ["id", "status", "title", "path"]
    rows = [
        (
            idea.id,
            idea.status,
            idea.title,
            relpath(idea.path, DEFAULT_ROOT),
        )
        for idea in ideas
    ]
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    fmt = " ".join(f"{{:<{width}}}" for width in widths)
    print(fmt.format(*headers))
    print("-" * (sum(widths) + len(widths) - 1))
    for row in rows:
        print(fmt.format(*row))
    if not rows:
        print("(no ideas found)")
    return 0


def _cmd_mark(args: Namespace) -> int:
    path = resolve_idea(args.target, Path(args.directory) if args.directory else IDEA_DIR)
    status = _ensure_status(args.status) if args.status else None
    layers = _normalize_layers(args.layer)
    systemic = _normalize_systemic(args.systemic)
    idea = _load_and_update(path, status=status, layers=layers, systemic=systemic, plan_id=args.plan_id)
    if args.title:
        idea.meta["title"] = args.title.strip()
    write_idea(idea)
    rel = relpath(path, DEFAULT_ROOT)
    print(f"updated {rel} → status={idea.meta.get('status')}")
    return 0


def _cmd_promote(args: Namespace) -> int:
    path = resolve_idea(args.target, Path(args.directory) if args.directory else IDEA_DIR)
    layers = _normalize_layers(args.layer)
    systemic = _normalize_systemic(args.systemic)
    idea = _load_and_update(path, status="promoted", layers=layers, systemic=systemic, plan_id=args.plan_id)
    if args.title:
        idea.meta["title"] = args.title.strip()
    if args.note:
        notes = idea.meta.get("notes")
        payload: list[str] = []
        if isinstance(notes, list):
            payload.extend(str(entry) for entry in notes)
        elif isinstance(notes, str):
            payload.append(notes)
        payload.append(args.note.strip())
        idea.meta["notes"] = payload
    write_idea(idea)
    rel = relpath(path, DEFAULT_ROOT)
    print(f"promoted {rel} → status=promoted")
    if args.plan_id:
        print(f"linked plan_id={args.plan_id}")
    else:
        print("hint: capture plan_id with --plan-id or update metadata when a plan is opened.")
    return 0


def _cmd_evaluate(args: Namespace) -> int:
    directory = Path(args.directory) if args.directory else IDEA_DIR
    ideas = iter_ideas(directory)
    if args.status:
        allowed = {_ensure_status(status) for status in args.status}
        ideas = [idea for idea in ideas if idea.status in allowed]
    if not args.include_promoted:
        ideas = [idea for idea in ideas if idea.status != "promoted"]

    scored = evaluate_ideas(ideas)
    if args.limit is not None and args.limit >= 0:
        scored = scored[: args.limit]

    if args.format == "json":
        payload = {
            "generated": _now_iso(),
            "count": len(scored),
            "ideas": [
                {
                    "id": entry["id"],
                    "title": entry["title"],
                    "status": entry["status"],
                    "score": entry["score"],
                    "layers": entry["layers"],
                    "systemic": entry["systemic"],
                    "plan_id": entry["plan_id"],
                    "path": relpath(entry["path"], DEFAULT_ROOT),
                    "reasons": entry["reasons"],
                    "updated": entry["updated"],
                    "created": entry["created"],
                }
                for entry in scored
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    headers = ["id", "score", "status", "layers", "systemic", "plan", "path"]
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    for entry in scored:
        rows.append(
            (
                entry["id"],
                f"{entry['score']:.2f}",
                entry["status"],
                ",".join(entry["layers"] or []),
                ",".join(str(s) for s in entry["systemic"] or []),
                entry["plan_id"] or "-",
                relpath(entry["path"], DEFAULT_ROOT),
            )
        )

    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    fmt = " ".join(f"{{:<{width}}}" for width in widths)
    print(fmt.format(*headers))
    print("-" * (sum(widths) + len(widths) - 1))
    for row, entry in zip(rows, scored):
        print(fmt.format(*row))
        if args.show_reasons:
            for reason in entry["reasons"]:
                print(f"  - {reason}")
    if not rows:
        print("(no ideas found)")
    return 0


def run(args: Namespace) -> int:
    command = getattr(args, "ideas_cmd", None)
    if command == "list":
        return _cmd_list(args)
    if command == "mark":
        return _cmd_mark(args)
    if command == "promote":
        return _cmd_promote(args)
    if command == "evaluate":
        return _cmd_evaluate(args)
    return 2


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    import argparse

    parser = subparsers.add_parser(
        "ideas",
        help="Manage idea lifecycle and promotion workflow",
    )
    idea_sub = parser.add_subparsers(dest="ideas_cmd", required=True)

    list_parser = idea_sub.add_parser(
        "list",
        help="List idea records (optionally filtered by status)",
    )
    list_parser.add_argument(
        "--status",
        action="append",
        help="Filter to specific statuses (repeatable)",
    )
    list_parser.add_argument(
        "--directory",
        type=Path,
        help="Override idea directory (tests/experiments)",
    )
    list_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
    )
    list_parser.set_defaults(func=run)

    mark_parser = idea_sub.add_parser(
        "mark",
        help="Update idea status or metadata",
    )
    mark_parser.add_argument("target", help="Idea identifier or path")
    mark_parser.add_argument(
        "--status",
        help=f"New status ({', '.join(VALID_STATUSES)})",
    )
    mark_parser.add_argument(
        "--layer",
        action="append",
        help="Associate layer target(s) (repeatable, e.g. --layer L4)",
    )
    mark_parser.add_argument(
        "--systemic",
        action="append",
        help="Associate systemic scale(s) 1..10 (repeatable)",
    )
    mark_parser.add_argument(
        "--plan-id",
        help="Link idea to an existing plan identifier",
    )
    mark_parser.add_argument(
        "--title",
        help="Update the idea title metadata",
    )
    mark_parser.add_argument(
        "--directory",
        type=Path,
        help="Override idea directory (tests/experiments)",
    )
    mark_parser.set_defaults(func=run)

    promote_parser = idea_sub.add_parser(
        "promote",
        help="Mark idea as promoted (optionally linking to a plan)",
    )
    promote_parser.add_argument("target", help="Idea identifier or path")
    promote_parser.add_argument(
        "--plan-id",
        help="Plan identifier capturing the promoted work",
    )
    promote_parser.add_argument(
        "--layer",
        action="append",
        help="Layer target(s) for the promoted scope",
    )
    promote_parser.add_argument(
        "--systemic",
        action="append",
        help="Systemic scale(s) for the promoted scope",
    )
    promote_parser.add_argument(
        "--title",
        help="Optional title override",
    )
    promote_parser.add_argument(
        "--note",
        help="Append rationale note to metadata",
    )
    promote_parser.add_argument(
        "--directory",
        type=Path,
        help="Override idea directory (tests/experiments)",
    )
    promote_parser.set_defaults(func=run)

    evaluate_parser = idea_sub.add_parser(
        "evaluate",
        help="Score ideas to recommend promotion candidates",
    )
    evaluate_parser.add_argument(
        "--status",
        action="append",
        help="Filter to specific statuses before scoring",
    )
    evaluate_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum ideas to display",
    )
    evaluate_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
    )
    evaluate_parser.add_argument(
        "--directory",
        type=Path,
        help="Override idea directory (tests/experiments)",
    )
    evaluate_parser.add_argument(
        "--include-promoted",
        action="store_true",
        help="Include already promoted ideas in scoring",
    )
    evaluate_parser.add_argument(
        "--show-reasons",
        action="store_true",
        help="Print scoring rationale in table output",
    )
    evaluate_parser.set_defaults(func=run)

    parser.set_defaults(func=run)


__all__ = ["register", "run"]
