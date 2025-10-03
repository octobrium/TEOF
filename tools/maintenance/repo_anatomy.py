"""Report repository anatomy (commit frequency, file counts, last touch)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_PATHS: Sequence[str] = (
    "docs",
    "tools",
    "_plans",
    "_report",
    "memory",
    "tests",
    "teof",
    "agents",
    "capsule",
)


def _run_git(args: Sequence[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def _commit_count(path: Path) -> int:
    try:
        output = _run_git(["rev-list", "--count", "HEAD", "--", str(path)])
        return int(output or 0)
    except subprocess.CalledProcessError:
        return 0


def _last_touch(path: Path) -> str | None:
    try:
        output = _run_git(["log", "-1", "--format=%ad", "--date=iso-strict", "--", str(path)])
        return output or None
    except subprocess.CalledProcessError:
        return None


def _file_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def collect_stats(paths: Sequence[str]) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    repo_root = Path.cwd()
    for slug in paths:
        target = repo_root / slug
        if not target.exists():
            continue
        stats = {
            "path": slug,
            "files": _file_count(target),
            "commits": _commit_count(target),
            "last_touch": _last_touch(target),
        }
        results.append(stats)
    return results


def _render_table(stats: Sequence[dict[str, object]]) -> str:
    if not stats:
        return "(no data)"
    headers = ["Path", "Files", "Commits", "Last Touch"]
    rows = [headers]
    for entry in stats:
        rows.append([
            entry["path"],
            str(entry["files"]),
            str(entry["commits"]),
            entry["last_touch"] or "-",
        ])
    widths = [max(len(row[idx]) for row in rows) for idx in range(len(headers))]
    lines = []
    for idx, row in enumerate(rows):
        padded = [value.ljust(widths[i]) for i, value in enumerate(row)]
        lines.append("  ".join(padded))
        if idx == 0:
            lines.append("  ".join("-" * width for width in widths))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paths",
        nargs="*",
        default=list(DEFAULT_PATHS),
        help="Directories to inspect (default: %(default)s)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--sort",
        choices=("commits", "files"),
        default="commits",
        help="Sort key for table/json output (default: commits)",
    )
    parser.add_argument(
        "--desc",
        action="store_true",
        help="Sort descending (default ascending)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write JSON summary to this path (directories created automatically)",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    stats = collect_stats(args.paths)
    stats.sort(key=lambda entry: entry[args.sort], reverse=args.desc)

    payload = {
        "generated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paths": stats,
    }

    if args.out is not None:
        destination = Path(args.out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {destination}")

    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(_render_table(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
