"""Detect verbal commitments that lack accompanying artifacts."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_PHRASES = ("next time", "mental note", "i'll remember", "later on")


def _iter_lines(paths: Iterable[Path]) -> Iterable[tuple[Path, int, str]]:
    for path in paths:
        try:
            with path.open(encoding="utf-8") as handle:
                for idx, line in enumerate(handle, 1):
                    yield path, idx, line.rstrip()
        except OSError:
            continue


def _match_phrases(text: str, phrases: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def scan(paths: Iterable[Path], phrases: Sequence[str]) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for path, lineno, line in _iter_lines(paths):
        if _match_phrases(line, phrases):
            matches.append(
                {
                    "path": str(path),
                    "line": lineno,
                    "excerpt": line.strip(),
                }
            )
    return matches


def default_paths() -> list[Path]:
    root = Path(__file__).resolve().parents[2]
    targets = [
        root / "_bus" / "messages",
        root / "_report" / "usage" / "reflection-intake",
    ]
    files: list[Path] = []
    for directory in targets:
        if directory.is_dir():
            files.extend(sorted(directory.glob("**/*.jsonl")))
            files.extend(sorted(directory.glob("**/*.md")))
    return files


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Files or directories to scan")
    parser.add_argument(
        "--phrases", nargs="*", default=list(DEFAULT_PHRASES), help="Phrases indicating commitments"
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)

    paths: list[Path] = []
    if args.paths:
        for path in args.paths:
            if path.is_dir():
                paths.extend(sorted(path.glob("**/*.jsonl")))
                paths.extend(sorted(path.glob("**/*.md")))
            else:
                paths.append(path)
    else:
        paths = default_paths()

    phrases = [phrase.lower() for phrase in args.phrases if phrase]
    results = scan(paths, phrases)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("commitment_guard: no unbacked commitments detected")
        else:
            print("commitment_guard: potential unbacked commitments detected")
            for match in results:
                print(f"- {match['path']}:{match['line']} — {match['excerpt']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
