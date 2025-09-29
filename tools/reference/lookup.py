
"""Quick lookup for TEOF references."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REF = ROOT / "docs" / "reference" / "quick-reference.md"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic", nargs="*", help="Topic keyword to search")
    parser.add_argument(
        "--json", action="store_true", help="Output JSON with matching lines"
    )
    return parser.parse_args(argv)


def load_reference() -> list[str]:
    if DEFAULT_REF.exists():
        return DEFAULT_REF.read_text(encoding="utf-8").splitlines()
    return []


def search(lines: list[str], keywords: list[str]) -> list[str]:
    if not keywords:
        return lines
    lowered = [k.lower() for k in keywords]
    matched: list[str] = []
    for line in lines:
        if all(k in line.lower() for k in lowered):
            matched.append(line)
    return matched


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    lines = load_reference()
    matches = search(lines, args.topic)
    if args.json:
        print(json.dumps({"matches": matches}, indent=2))
    else:
        for line in matches:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
