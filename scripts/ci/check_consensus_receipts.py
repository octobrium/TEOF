#!/usr/bin/env python3
"""Validate consensus receipt summary and underlying artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_PATH = ROOT / "_report" / "consensus" / "summary-latest.json"


def _load_summary(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"missing consensus summary: {path.relative_to(ROOT)}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"summary must be a JSON object: {path.relative_to(ROOT)}")
    return data


def _validate_summary(data: dict) -> list[str]:
    errors: list[str] = []
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return ["summary-latest.json missing 'tasks' list"]
    for idx, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            errors.append(f"tasks[{idx}] must be object")
            continue
        task_id = task.get("task_id")
        receipts = task.get("required_receipts")
        if not isinstance(task_id, str) or not task_id.strip():
            errors.append(f"tasks[{idx}] missing task_id")
        if not isinstance(receipts, list) or not receipts:
            errors.append(f"tasks[{idx}] must list required_receipts")
            continue
        for receipt in receipts:
            if not isinstance(receipt, str) or not receipt.strip():
                errors.append(f"tasks[{idx}] has invalid receipt entry {receipt!r}")
                continue
            receipt_path = ROOT / receipt
            if not receipt_path.exists():
                errors.append(
                    f"required receipt missing for {task_id or f'tasks[{idx}]'}: {receipt}"
                )
    return errors


def main() -> int:
    try:
        summary = _load_summary(SUMMARY_PATH)
    except (FileNotFoundError, ValueError) as exc:
        print(f"::error::{exc}")
        return 1

    errors = _validate_summary(summary)
    if errors:
        for err in errors:
            print(f"::error::{err}")
        return 1

    print("::notice::consensus receipts verified")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
