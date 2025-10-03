#!/usr/bin/env python3
"""Generate a receipt summarising planner queue warnings."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from tools.planner import queue_warnings

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_SUBDIR = Path("_report") / "planner" / "queue-warnings"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _render_markdown(warnings: List[dict[str, object]]) -> str:
    lines = ["# Planner Queue Warning Scan — " + _iso_now(), ""]
    if not warnings:
        lines.append("No queue mismatches detected")
        return "\n".join(lines) + "\n"
    headers = ("plan", "queue", "issue", "message")
    widths = [len(header) for header in headers]
    rows: List[tuple[str, str, str, str]] = []
    for warning in warnings:
        plan_id = str(warning.get("plan_id", "-"))
        queue_ref = str(warning.get("queue_ref", "-"))
        issue = str(warning.get("issue", "-"))
        message = str(warning.get("message", "-"))
        row = (plan_id, queue_ref, issue, message)
        rows.append(row)
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    header_line = " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    divider = " | ".join("-" * widths[idx] for idx in range(len(headers)))
    lines.extend((header_line, divider))
    for row in rows:
        lines.append(
            " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row))
        )
    return "\n".join(lines) + "\n"


def _render_json(warnings: List[dict[str, object]]) -> str:
    payload = {
        "generated_at": _iso_now(),
        "warnings": warnings,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _default_output_path(fmt: str) -> Path:
    out_dir = ROOT / OUTPUT_SUBDIR
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = "md" if fmt == "markdown" else "json"
    return out_dir / f"scan-{stamp}.{suffix}"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--out", help="Optional output file path")
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with status 1 when warnings exist",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    warnings = queue_warnings.load_queue_warnings(ROOT)

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = (ROOT / out_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        out_path = _default_output_path(args.format)

    if args.format == "markdown":
        content = _render_markdown(warnings)
    else:
        content = _render_json(warnings)
    out_path.write_text(content, encoding="utf-8")
    try:
        rel = out_path.relative_to(ROOT)
    except ValueError:
        rel = out_path
    print(rel)

    if args.fail_on_warning and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
