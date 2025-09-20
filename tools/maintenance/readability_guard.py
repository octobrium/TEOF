#!/usr/bin/env python3
"""Measure basic readability metrics for key documentation surfaces."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "_report" / "readability"
SUMMARY_PATH = REPORT_DIR / "summary-latest.json"
DEFAULT_TARGETS = [
    ROOT / "docs" / "architecture.md",
    ROOT / "docs" / "decision-hierarchy.md",
    ROOT / "docs" / "quick-links.md",
    ROOT / "docs" / "maintenance" / "capsule-cadence.md",
]


SENTENCE_SPLIT_RE = re.compile(r"[.!?]+\s+|", re.MULTILINE)
WORD_RE = re.compile(r"[A-Za-z0-9']+")


def average_sentence_length(text: str) -> float:
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        return 0.0
    total_words = sum(len(WORD_RE.findall(sentence)) for sentence in sentences)
    return total_words / max(len(sentences), 1)


def average_word_length(text: str) -> float:
    words = WORD_RE.findall(text)
    if not words:
        return 0.0
    return sum(len(word) for word in words) / len(words)


def analyse_file(path: Path, *, sentence_threshold: float, word_threshold: float) -> dict:
    text = path.read_text(encoding="utf-8")
    sent_len = average_sentence_length(text)
    word_len = average_word_length(text)
    return {
        "path": str(path.relative_to(ROOT)),
        "avg_sentence_words": sent_len,
        "avg_word_length": word_len,
        "pass": sent_len <= sentence_threshold and word_len <= word_threshold,
        "sentence_threshold": sentence_threshold,
        "word_threshold": word_threshold,
    }


def run(targets: Iterable[Path], *, sentence_threshold: float, word_threshold: float) -> list[dict]:
    results: list[dict] = []
    for path in targets:
        if not path.exists():
            results.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "error": "missing",
                    "pass": False,
                }
            )
            continue
        results.append(
            analyse_file(
                path,
                sentence_threshold=sentence_threshold,
                word_threshold=word_threshold,
            )
        )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute readability metrics for docs")
    parser.add_argument("paths", nargs="*", help="Specific files to analyse (defaults to key docs)")
    parser.add_argument(
        "--sentence-threshold",
        type=float,
        default=25.0,
        help="Maximum average words per sentence (default: %(default)s)",
    )
    parser.add_argument(
        "--word-threshold",
        type=float,
        default=6.0,
        help="Maximum average characters per word (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    targets = [ROOT / p for p in args.paths] if args.paths else DEFAULT_TARGETS
    results = run(targets, sentence_threshold=args.sentence_threshold, word_threshold=args.word_threshold)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(
        json.dumps(
            {
                "generated_at": __import__("datetime").datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    failures = [item for item in results if not item.get("pass", True)]
    if failures:
        for item in failures:
            if item.get("error") == "missing":
                print(f"::error::readability target missing: {item['path']}")
            else:
                print(
                    f"::error::{item['path']} readability fail: avg_sentence_words={item['avg_sentence_words']:.2f}",
                )
        return 1

    print("::notice::readability guard passed")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
