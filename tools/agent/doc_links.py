#!/usr/bin/env python3
"""Expose high-traffic documentation anchors via a quick-link helper."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from tools.usage.logger import record_usage

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "docs" / "quick-links.json"
DEFAULT_LIST_FORMAT = "table"
DEFAULT_SHOW_FORMAT = "plain"
VALID_LIST_FORMATS = {"table", "json"}
VALID_SHOW_FORMATS = {"plain", "json"}


@dataclass
class QuickLink:
    id: str
    title: str
    summary: str
    path: str
    anchor: str
    category: str | None = None

    @property
    def target(self) -> str:
        anchor = self.anchor or ""
        return f"{self.path}{anchor}"

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "path": self.path,
            "anchor": self.anchor,
            "target": self.target,
        }
        if self.category:
            payload["category"] = self.category
        return payload


class ManifestError(RuntimeError):
    """Raised when the manifest is missing or invalid."""


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _ensure_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ManifestError(f"Manifest missing: {_display_path(path)}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Invalid JSON in {_display_path(path)}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ManifestError("Manifest root must be an object")
    return raw


def _load_links(data: dict[str, Any]) -> tuple[int, str, list[QuickLink]]:
    version = data.get("version")
    if not isinstance(version, int):
        raise ManifestError("Manifest missing integer 'version'")
    updated = data.get("updated")
    if not isinstance(updated, str) or not updated:
        raise ManifestError("Manifest missing 'updated' string")
    raw_links = data.get("links")
    if not isinstance(raw_links, list):
        raise ManifestError("Manifest 'links' must be a list")

    links: list[QuickLink] = []
    seen_ids: set[str] = set()

    for entry in raw_links:
        if not isinstance(entry, dict):
            raise ManifestError("Each link entry must be an object")
        link_id = entry.get("id")
        title = entry.get("title")
        summary = entry.get("summary")
        path = entry.get("path")
        anchor = entry.get("anchor")
        category = entry.get("category")
        if not all(isinstance(value, str) and value for value in (link_id, title, summary, path)):
            raise ManifestError(f"Link entry missing required string fields: {entry}")
        if not isinstance(anchor, str) or not anchor.startswith("#"):
            raise ManifestError(f"Link '{link_id}' has invalid anchor '{anchor}'")
        if category is not None and not isinstance(category, str):
            raise ManifestError(f"Link '{link_id}' has non-string category")
        if link_id in seen_ids:
            raise ManifestError(f"Duplicate link id '{link_id}'")
        seen_ids.add(link_id)

        links.append(
            QuickLink(
                id=link_id,
                title=title,
                summary=summary,
                path=path,
                anchor=anchor,
                category=category,
            )
        )

    links.sort(key=lambda item: item.id)
    return version, updated, links


def load_manifest(path: Path | None = None) -> tuple[int, str, list[QuickLink]]:
    manifest_path = path or MANIFEST_PATH
    data = _ensure_manifest(manifest_path)
    return _load_links(data)


def _format_table(rows: Iterable[dict[str, str]], columns: Sequence[tuple[str, str]]) -> str:
    rows_list = list(rows)
    widths = []
    for key, header in columns:
        width = len(header)
        for row in rows_list:
            width = max(width, len(row.get(key, "")))
        widths.append(width)

    header_line = " | ".join(header.ljust(width) for (_, header), width in zip(columns, widths))
    divider = "-+-".join("-" * width for width in widths)
    lines = [header_line, divider]
    for row in rows_list:
        line = " | ".join(row.get(key, "").ljust(width) for (key, _), width in zip(columns, widths))
        lines.append(line.rstrip())
    return "\n".join(lines)


def handle_list(args: argparse.Namespace) -> None:
    version, updated, links = load_manifest()
    if args.category:
        category = args.category.lower().strip()
        links = [link for link in links if (link.category or '').lower() == category]
    if args.format not in VALID_LIST_FORMATS:
        raise SystemExit(f"Unsupported format '{args.format}'. Choose from: {sorted(VALID_LIST_FORMATS)}")

    if args.format == "json":
        payload = {
            "version": version,
            "updated": updated,
            "links": [link.to_payload() for link in links],
            "category": args.category,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    rows = [
        {
            "id": link.id,
            "title": link.title,
            "target": link.target,
            "category": link.category or "-",
        }
        for link in links
    ]
    columns = (
        ("id", "id"),
        ("title", "title"),
        ("target", "target"),
        ("category", "category"),
    )
    table = _format_table(rows, columns)
    print(f"Docs quick-links (version {version}, updated {updated})")
    print(table)


def handle_show(args: argparse.Namespace) -> None:
    version, updated, links = load_manifest()
    if args.format not in VALID_SHOW_FORMATS:
        raise SystemExit(f"Unsupported format '{args.format}'. Choose from: {sorted(VALID_SHOW_FORMATS)}")

    link = next((item for item in links if item.id == args.link_id), None)
    if link is None:
        raise SystemExit(f"Unknown link id '{args.link_id}'. Run 'doc_links list' to inspect available ids.")

    if args.format == "json":
        print(json.dumps(link.to_payload(), indent=2, sort_keys=True))
        return

    print(f"{link.title} [{link.id}]")
    print(f"Category: {link.category or '-'}")
    print(f"Target: {link.target}")
    print(f"Summary: {link.summary}")
    print(f"Manifest version: {version} (updated {updated})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List all quick-link entries")
    list_parser.add_argument(
        "--format",
        choices=sorted(VALID_LIST_FORMATS),
        default=DEFAULT_LIST_FORMAT,
        help="Output format (default: table)",
    )
    list_parser.add_argument(
        "--category",
        help="Filter results to a specific category (e.g., quickstart, coordination)",
    )
    list_parser.set_defaults(func=handle_list)

    show_parser = subparsers.add_parser("show", help="Show a single quick-link entry")
    show_parser.add_argument("link_id", help="Quick-link id to display")
    show_parser.add_argument(
        "--format",
        choices=sorted(VALID_SHOW_FORMATS),
        default=DEFAULT_SHOW_FORMAT,
        help="Output format (default: plain)",
    )
    show_parser.set_defaults(func=handle_show)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        args.func(args)
    except ManifestError as exc:
        raise SystemExit(f"Manifest error: {exc}") from exc

    extra: dict[str, Any] = {}
    if args.command == "list":
        extra = {"format": args.format}
        if args.category:
            extra["category"] = args.category
    elif args.command == "show":
        extra = {"format": args.format, "id": args.link_id}
    record_usage("agent.doc_links", action=args.command, extra=extra)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
