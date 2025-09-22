"""Suggest or claim the next development task when guardrails are satisfied."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping

from tools.autonomy import actions, audit_guidelines, backlog_synth, health_sensors

ROOT = Path(__file__).resolve().parents[2]
TODO_PATH = ROOT / "_plans" / "next-development.todo.json"
AUTH_JSON = ROOT / "_report" / "usage" / "external-authenticity.json"
STATUS_PATH = ROOT / "_report" / "planner" / "validate" / "summary-latest.json"
CONSENT_POLICY_PATH = ROOT / "docs" / "automation" / "autonomy-consent.json"


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


def _load_policy(path: Path = CONSENT_POLICY_PATH) -> Mapping[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, Mapping):
            return data
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        pass
    return {
        "auto_enabled": False,
        "max_iterations": 1,
        "require_execute": True,
        "allow_apply": False,
        "halt_on_attention_feeds": True,
        "halt_on_ci_failure": True,
    }


def _preflight(todo_path: Path) -> Mapping[str, object] | None:
    health_report = health_sensors.emit_health_report()
    synth = backlog_synth.synthesise(todo_path=todo_path)
    audit = audit_guidelines.audit_layers(todo_path=todo_path)
    return {
        "health_report": str(health_report.relative_to(ROOT)),
        "synth": synth,
        "audit": str(audit.relative_to(ROOT)),
    }


def _execute_action(item: Mapping[str, object], *, apply_changes: bool) -> Mapping[str, object] | None:
    plan_id = item.get("plan_suggestion")
    if not isinstance(plan_id, str):
        return None
    action = actions.resolve(plan_id)
    if action is None:
        return None
    outcome = action(root=ROOT, dry_run=not apply_changes)
    if outcome is None:
        return None
    serialisable = dict(outcome)
    path_value = serialisable.get("report_path")
    if isinstance(path_value, Path):
        try:
            serialisable["report_path"] = str(path_value.relative_to(ROOT))
        except ValueError:
            serialisable["report_path"] = str(path_value)
    return serialisable


def _run_once(
    *,
    claim: bool,
    execute: bool,
    apply_changes: bool,
    skip_synth: bool,
) -> Mapping[str, object] | None:
    preflight = None
    if not skip_synth:
        preflight = _preflight(TODO_PATH)
    item = select_next_step(
        claim=claim,
        todo_path=TODO_PATH,
        auth_json=AUTH_JSON,
        status_path=STATUS_PATH,
        allow_failure=True,
    )
    if item is None:
        return None
    payload: Mapping[str, object] = dict(item)
    if preflight is not None:
        payload = dict(payload)
        payload["preflight"] = preflight
    if execute:
        action_result = _execute_action(item, apply_changes=apply_changes)
        if action_result is not None:
            payload = dict(payload)
            payload["action"] = action_result
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim", action="store_true", help="Mark the first pending item as in-progress")
    parser.add_argument("--out", type=Path, help="Optional path to write the selected item JSON")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Attempt to execute the action associated with the selected plan",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Allow actions to modify the repository (default runs in dry-run mode)",
    )
    parser.add_argument(
        "--skip-synth",
        action="store_true",
        help="Skip backlog synthesis/audit before selection",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically loop through backlog according to consent policy",
    )
    args = parser.parse_args(argv)

    if args.auto:
        policy = _load_policy()
        if not policy.get("auto_enabled"):
            raise NextStepError("Auto mode disabled in policy")
        execute = args.execute or bool(policy.get("require_execute", False))
        apply_changes = args.apply and bool(policy.get("allow_apply", False))
        max_iterations = int(policy.get("max_iterations", 1))
        results: List[Mapping[str, object]] = []
        for _ in range(max_iterations):
            payload = _run_once(
                claim=True,
                execute=execute,
                apply_changes=apply_changes,
                skip_synth=args.skip_synth,
            )
            if payload is None:
                break
            results.append(payload)
            if not policy.get("continuous", False):
                break
        if not results:
            raise NextStepError("No pending items found")
        output = {"runs": results}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        if args.out:
            args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0

    payload = _run_once(
        claim=args.claim,
        execute=args.execute,
        apply_changes=args.apply,
        skip_synth=args.skip_synth,
    )
    if payload is None:
        raise NextStepError("No pending items found")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.out:
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NextStepError as exc:
        print(f"next-step error: {exc}", file=sys.stderr)
        raise SystemExit(1)
