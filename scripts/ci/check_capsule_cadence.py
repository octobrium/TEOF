#!/usr/bin/env python3
"""Guard capsule cadence by validating required receipts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_PATH = ROOT / "_report" / "capsule" / "summary-latest.json"


def _load_summary(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"missing capsule summary: {path.relative_to(ROOT)}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"summary must be a JSON object: {path.relative_to(ROOT)}")
    return data


def _extract_receipts(data: dict) -> list[str]:
    receipts: list[str] = []
    required = data.get("required_receipts")
    if isinstance(required, list):
        receipts.extend(str(item) for item in required if isinstance(item, str) and item.strip())
    consensus = data.get("consensus_summary")
    if isinstance(consensus, str) and consensus.strip():
        receipts.append(consensus.strip())
    return receipts


def _validate_summary(path: Path, data: dict) -> list[str]:
    errors: list[str] = []
    receipts = _extract_receipts(data)
    if not receipts:
        errors.append(
            f"{path.relative_to(ROOT)} must list at least one receipt under 'required_receipts' or 'consensus_summary'"
        )
        return errors
    for receipt in receipts:
        receipt_path = ROOT / receipt
        if not receipt_path.exists():
            errors.append(f"capsule cadence missing receipt: {receipt}")
    return errors


def main() -> int:
    try:
        summary = _load_summary(SUMMARY_PATH)
    except (FileNotFoundError, ValueError) as exc:
        print(f"::error::{exc}")
        return 1

    errors = _validate_summary(SUMMARY_PATH, summary)
    if errors:
        for err in errors:
            print(f"::error::{err}")
        return 1

    print("::notice::capsule cadence receipts verified")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
