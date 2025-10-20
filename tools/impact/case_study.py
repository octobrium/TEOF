"""Summaries for case study receipts."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from tools.autonomy.shared import load_backlog_items


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SLUG = "relay-insight"
ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True)
class ArtifactGroup:
    """Describes artifact patterns tracked for a case study."""

    name: str
    patterns: tuple[str, ...]
    kind: str  # "json" or "text"
    required: bool = False


ARTIFACT_GROUPS: tuple[ArtifactGroup, ...] = (
    ArtifactGroup("consent", ("consent.json",), "json", required=True),
    ArtifactGroup("dry_runs", ("conductor-dry-run-*.json",), "json", required=True),
    ArtifactGroup(
        "live_runs",
        ("conductor-run-*.json", "run-*.json"),
        "json",
        required=True,
    ),
    ArtifactGroup(
        "command_logs",
        (
            "commands-*.json",
            "command-log-*.json",
            "commands-*.log",
            "command-log-*.log",
            "commands-*.md",
            "command-log-*.md",
        ),
        "text",
        required=True,
    ),
    ArtifactGroup("diffs", ("diffs-*.json", "diff-*.json"), "json"),
    ArtifactGroup(
        "tests",
        ("pytest-*.json", "tests-*.json", "pytest-*.log", "tests-*.log"),
        "text",
    ),
)


def _now_iso() -> str:
    return dt.datetime.utcnow().strftime(ISO_FORMAT)


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path.resolve())


def _load_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(data, dict):
        return data
    return None


def _collect_files(base: Path, patterns: Sequence[str]) -> list[Path]:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(base.glob(pattern))
    return sorted(set(matches))


def _summarise_json_file(
    path: Path,
    root: Path,
    task_status: dict[str, str] | None = None,
) -> dict[str, object]:
    info: dict[str, object] = {
        "path": _relative(path, root),
        "size_bytes": path.stat().st_size,
    }
    payload = _load_json(path)
    if payload is None:
        info["warning"] = "invalid json"
        return info

    for field in ("generated_at", "captured_at", "summary_generated_at"):
        value = payload.get(field)
        if isinstance(value, str):
            info[field] = value

    task = payload.get("task")
    if isinstance(task, dict):
        task_info = {
            key: task.get(key)
            for key in ("id", "title", "status")
            if task.get(key) is not None
        }
        task_id = task_info.get("id")
        override = None
        if task_status and isinstance(task_id, str):
            override = task_status.get(task_id)
        if override and task_info.get("status") != override:
            task_info["status"] = override
            task_info["status_source"] = "_plans/next-development.todo.json"
        if task_info:
            info["task"] = task_info

    guardrails = payload.get("guardrails")
    if isinstance(guardrails, dict):
        snapshot = {
            key: guardrails.get(key)
            for key in ("diff_limit", "tests", "receipts_dir")
            if guardrails.get(key) is not None
        }
        if snapshot:
            info["guardrails"] = snapshot

    return info


def _summarise_text_file(path: Path, root: Path) -> dict[str, object]:
    return {
        "path": _relative(path, root),
        "size_bytes": path.stat().st_size,
    }


def _load_task_statuses(root: Path) -> dict[str, str]:
    """Return latest task statuses from backlog (active + archive)."""

    path = root / "_plans" / "next-development.todo.json"
    items = load_backlog_items(path, include_archive=True)
    statuses: dict[str, str] = {}
    for item in items:
        task_id = item.get("id")
        status = item.get("status")
        if isinstance(task_id, str) and isinstance(status, str):
            statuses[task_id] = status
    return statuses


def build_summary(slug: str = DEFAULT_SLUG, *, root: Path | None = None) -> dict[str, object]:
    """Collect receipts for ``slug`` and produce a structured summary."""

    root = root or ROOT
    case_dir = root / "_report" / "usage" / "case-study" / slug
    if not case_dir.exists():
        raise FileNotFoundError(f"case study directory not found: {case_dir}")

    artifact_status: dict[str, dict[str, object]] = {}
    missing: list[str] = []
    task_statuses = _load_task_statuses(root)

    for group in ARTIFACT_GROUPS:
        files = _collect_files(case_dir, group.patterns)
        if group.kind == "json":
            items = [
                _summarise_json_file(path, root, task_status=task_statuses)
                for path in files
            ]
        else:
            items = [_summarise_text_file(path, root) for path in files]

        status: dict[str, object] = {
            "present": bool(files),
            "count": len(files),
            "items": items,
        }
        artifact_status[group.name] = status

        if group.required and not files:
            missing.append(group.name)

    notes: list[str] = []
    if missing:
        notes.append(
            "Missing required receipts: " + ", ".join(sorted(missing)) + "."
        )
        notes.append(
            "Capture live sprint data via `_plans/2025-09-27-relay-case-run` (steps S2–S3)."
        )

    notes.append(
        f"Re-run `python -m tools.impact.case_study summarize --slug {slug}` after adding new receipts."
    )

    summary: dict[str, object] = {
        "generated_at": _now_iso(),
        "slug": slug,
        "case_dir": _relative(case_dir, root),
        "artifact_status": artifact_status,
        "missing_requirements": sorted(missing),
        "notes": notes,
    }
    return summary


def write_summary(summary: dict[str, object], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def _summarise_command(slug: str, out: Path | None, root: Path | None = None) -> int:
    summary = build_summary(slug, root=root)
    if out is not None:
        if not out.is_absolute():
            out = (root or ROOT) / out
        path = write_summary(summary, out)
        print(f"wrote { _relative(path, root or ROOT) }")
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.impact.case_study",
        description="Summarise case study receipts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    summarise = sub.add_parser(
        "summarize", help="Generate a summary for a case study slug"
    )
    summarise.add_argument("--slug", default=DEFAULT_SLUG)
    summarise.add_argument(
        "--out",
        type=Path,
        help="Optional path to write JSON summary (defaults to stdout).",
    )
    summarise.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Override repository root (tests-only).",
    )
    summarise.set_defaults(func=_cmd_summarize)

    return parser


def _cmd_summarize(args: argparse.Namespace) -> int:
    root = args.root if args.root is not None else ROOT
    return _summarise_command(args.slug, args.out, root=root)


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    func = getattr(args, "func", None)
    if not callable(func):
        parser.print_help()
        return 2
    return func(args)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_summary", "write_summary", "main"]
