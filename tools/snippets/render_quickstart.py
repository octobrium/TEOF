#!/usr/bin/env python3
"""Render the canonical Quickstart snippet into markdown."""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

ROOT = pathlib.Path(__file__).resolve().parents[2]
SNIPPET_JSON = ROOT / "tools" / "snippets" / "quickstart.json"
DEFAULT_OUT = ROOT / "docs" / "_generated" / "quickstart_snippet.md"


def load_commands() -> dict:
    payload = json.loads(SNIPPET_JSON.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("snippet payload must be an object")
    payload.setdefault("commands", [])
    payload.setdefault("notes", [])
    return payload


def render_markdown(commands: Sequence[str], notes: Sequence[str]) -> str:
    lines = [
        "<!-- generated: quickstart snippet -->",
        "Run this smoke test on a fresh checkout:",
        "```bash",
    ]
    lines.extend(commands)
    lines.append("```")
    if notes:
        lines.append("")
        lines.extend(f"- {note}" for note in notes)
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render quickstart snippet")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output path for markdown snippet")
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = load_commands()
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_markdown(payload["commands"], payload["notes"]),
        encoding="utf-8",
    )
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
