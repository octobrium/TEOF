#!/usr/bin/env python3
"""Fail CI when readability summary reports any failing documents."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_PATH = ROOT / "_report" / "readability" / "summary-latest.json"


def main() -> int:
    if not SUMMARY_PATH.exists():
        print(f"::error::missing readability summary: {SUMMARY_PATH.relative_to(ROOT)}")
        return 1
    try:
        data = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"::error::invalid readability summary: {exc}")
        return 1

    results = data.get("results")
    if not isinstance(results, list):
        print("::error::readability summary missing 'results' list")
        return 1

    failures = [item for item in results if not item.get("pass", True)]
    if failures:
        for item in failures:
            path = item.get("path", "unknown")
            if item.get("error") == "missing":
                print(f"::error::readability target missing: {path}")
            else:
                print(
                    f"::error::{path} readability fail: avg_sentence_words={item.get('avg_sentence_words')} avg_word_length={item.get('avg_word_length')}"
                )
        return 1

    print("::notice::readability summary clean")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
