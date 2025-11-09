#!/usr/bin/env python3
"""Enforce minimum coverage based on coverage.xml."""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_COVERAGE_XML = Path("coverage.xml")
DEFAULT_THRESHOLD = 0.70


class CoverageError(RuntimeError):
    """Raised when coverage data is missing or below threshold."""


def _threshold_arg(value: str) -> float:
    try:
        threshold = float(value)
    except ValueError as exc:  # pragma: no cover - argparse catches
        raise argparse.ArgumentTypeError("--threshold must be a number between 0.0 and 1.0") from exc
    if not 0.0 <= threshold <= 1.0:
        raise argparse.ArgumentTypeError("--threshold must be between 0.0 and 1.0")
    return threshold


def parse_coverage_rate(path: Path) -> float:
    if not path.exists():
        raise CoverageError(f"coverage file missing: {path}")
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise CoverageError(f"invalid coverage XML ({path}): {exc}") from exc
    root = tree.getroot()
    rate = root.attrib.get("line-rate")
    if rate is None:
        raise CoverageError(f"coverage XML missing line-rate attribute: {path}")
    try:
        return float(rate)
    except ValueError as exc:
        raise CoverageError(f"invalid line-rate value '{rate}' in {path}") from exc


def enforce_threshold(rate: float, threshold: float) -> None:
    if rate < threshold:
        raise CoverageError(f"coverage {rate:.3f} below threshold {threshold:.3f}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fail when coverage.xml falls below threshold")
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_COVERAGE_XML,
        help=f"Coverage XML to parse (default: {DEFAULT_COVERAGE_XML})",
    )
    parser.add_argument(
        "--threshold",
        type=_threshold_arg,
        default=DEFAULT_THRESHOLD,
        help=f"Minimum line-rate required (default: {DEFAULT_THRESHOLD:.2f})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress success message (still prints errors on failure)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        rate = parse_coverage_rate(args.path)
        enforce_threshold(rate, args.threshold)
    except CoverageError as exc:
        print(f"coverage_guard: {exc}", file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"coverage_guard: {rate:.3%} >= {args.threshold:.3%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
