"""Validate minimal TEOF semantic patch payloads."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Tuple


def _error(message: str) -> Tuple[bool, str]:
    return False, message


def validate(payload: dict) -> Tuple[bool, str]:
    if not isinstance(payload, dict):
        return _error("payload must be a JSON object")

    for key in ("work_id", "edits", "tests", "rollback"):
        if key not in payload:
            return _error(f"missing required field '{key}'")

    if not isinstance(payload["work_id"], str) or not payload["work_id"].strip():
        return _error("work_id must be a non-empty string")

    edits = payload["edits"]
    if not isinstance(edits, list) or not edits:
        return _error("edits must be a non-empty array")
    for idx, edit in enumerate(edits, 1):
        if not isinstance(edit, dict):
            return _error(f"edit #{idx} must be an object")
        for field in ("path", "selector", "operation"):
            if field not in edit:
                return _error(f"edit #{idx} missing '{field}'")
        if edit["operation"] not in {"insert", "replace", "remove"}:
            return _error(f"edit #{idx} has invalid operation '{edit['operation']}'")

    tests = payload["tests"]
    if not isinstance(tests, list):
        return _error("tests must be an array")
    if not all(isinstance(item, str) for item in tests):
        return _error("tests entries must be strings")

    rollback = payload["rollback"]
    if not isinstance(rollback, dict):
        return _error("rollback must be an object")
    if "instructions" not in rollback or not isinstance(rollback["instructions"], str):
        return _error("rollback.instructions must be a string")

    return True, "semantic patch payload is valid"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to semantic patch JSON")
    parser.add_argument("--summary", action="store_true", help="Print a human-readable summary when valid")
    return parser.parse_args(list(argv) if argv is not None else None)


def _summarise(payload: dict) -> str:
    lines = [f"work_id: {payload['work_id']}"]
    lines.append(f"edits: {len(payload['edits'])}")
    tests = payload.get("tests", [])
    if tests:
        lines.append("tests: " + ", ".join(tests))
    rollback = payload.get("rollback", {}).get("instructions")
    if rollback:
        lines.append("rollback: " + rollback.splitlines()[0])
    return " | ".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: file not found: {args.input}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}")
        return 2

    ok, message = validate(payload)
    if not ok:
        print(f"error: {message}")
        return 1

    print(message)
    if args.summary:
        print(_summarise(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
