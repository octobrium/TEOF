"""CLI for generating TEOF philosophical alignment prompts."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from extensions.prompts.philosophy import build_prompt

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "_report" / "usage" / "prompts"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Question to align against TEOF philosophy")
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional path to write the prompt (default: _report/usage/prompts/philosophy-<UTC>.md)",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    prompt = build_prompt(args.question)
    if args.out:
        output_path = args.out
    else:
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timezone

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = DEFAULT_OUTPUT_DIR / f"philosophy-{stamp}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(prompt + "\n", encoding="utf-8")
    print(str(output_path.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
