#!/usr/bin/env python3
"""Show semantic diff for commandments documents."""
from __future__ import annotations

import argparse
import difflib
from pathlib import Path


def load_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff two commandments documents")
    parser.add_argument("left", help="Path to local commandments.md")
    parser.add_argument("right", help="Path to peer commandments.md")
    args = parser.parse_args()

    left_path = Path(args.left)
    right_path = Path(args.right)
    left = load_lines(left_path)
    right = load_lines(right_path)

    diff = difflib.unified_diff(left, right, fromfile=str(left_path), tofile=str(right_path), lineterm="")
    has_diff = False
    for line in diff:
        has_diff = True
        print(line)
    return 1 if has_diff else 0


if __name__ == "__main__":
    raise SystemExit(main())
