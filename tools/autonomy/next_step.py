"""Suggest or claim the next development task when guardrails are satisfied."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
TODO_PATH = ROOT / "_plans" / "next-development.todo.json"
AUTH_JSON = ROOT / "_report" / "usage" / "external-authenticity.json"
STATUS_PATH = ROOT / "_report" / "planner" / "validate" / "summary-latest.json"


class NextStepError(RuntimeError):
    """Raised when next automation step cannot be determined."""


def _load_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _pick_item(todo: Dict[str, Any]) -> Dict[str, Any] | None:
    for item in todo.get("items", []):
        if item.get("status") == "pending":
            return item
    return None


def _auth_ok(auth: Dict[str, Any] | None, min_trust: float, require_no_attention: bool) -> bool:
    if auth is None:
        return False
    overall = auth.get("overall_avg_trust")
    if overall is None or not isinstance(overall, (int, float)):
        return False
    if overall < min_trust:
        return False
    if require_no_attention:
        attention = auth.get("attention_feeds", [])
        if isinstance(attention, list) and attention:
            return False
    return True


def _ci_ok(status_path: Path) -> bool:
    status = _load_json(status_path)
    if not status:
        return True
    state = status.get("status")
    if isinstance(state, str):
        return state.lower() == "ok"
    exit_code = status.get("exit_code")
    if isinstance(exit_code, int):
        return exit_code == 0
    return True


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def select_next_step(
    *,
    claim: bool = False,
    todo_path: Path | None = None,
    auth_json: Path | None = None,
    status_path: Path | None = None,
    allow_failure: bool = True,
) -> Dict[str, Any] | None:
    todo_path = todo_path or TODO_PATH
    auth_json = auth_json or AUTH_JSON
    status_path = status_path or STATUS_PATH

    todo = _load_json(todo_path)
    if not todo:
        if allow_failure:
            return None
        raise NextStepError(f"todo file missing or invalid: {todo_path}")

    prerequisites = todo.get("prerequisites", {})
    min_trust = float(prerequisites.get("min_overall_trust", 0.7))
    require_no_attention = bool(prerequisites.get("require_no_attention_feeds", True))

    authenticity = _load_json(auth_json)
    if not _auth_ok(authenticity, min_trust, require_no_attention):
        if allow_failure:
            return None
        raise NextStepError("Authenticity prerequisites not met")

    if not _ci_ok(status_path):
        if allow_failure:
            return None
        raise NextStepError("CI summary not OK")

    item = _pick_item(todo)
    if not item:
        if allow_failure:
            return None
        raise NextStepError("No pending items found")

    selected = dict(item)

    if claim:
        item["status"] = "in_progress"
        history_entry = {
            "id": item.get("id"),
            "claimed_at": _iso_now(),
        }
        todo.setdefault("history", []).append(history_entry)
        todo_path.write_text(json.dumps(todo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim", action="store_true", help="Mark the first pending item as in-progress")
    parser.add_argument("--out", type=Path, help="Optional path to write the selected item JSON")
    args = parser.parse_args(argv)

    item = select_next_step(
        claim=args.claim,
        todo_path=TODO_PATH,
        auth_json=AUTH_JSON,
        status_path=STATUS_PATH,
        allow_failure=False,
    )
    if args.out:
        args.out.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(item, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NextStepError as exc:
        print(f"next-step error: {exc}", file=sys.stderr)
        raise SystemExit(1)
