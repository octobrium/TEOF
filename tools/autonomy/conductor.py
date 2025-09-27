"""Guarded conductor for orchestrating Codex-driven refinements."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping

from tools.autonomy import next_step, objectives_status, preflight as preflight_mod


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "_report" / "usage" / "autonomy-conductor"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_prompt(task: Mapping[str, Any], guardrails: Mapping[str, Any]) -> str:
    notes = task.get("notes", "")
    plan = task.get("plan_suggestion", "unknown")
    return (
        "You are Codex acting as an autonomy engineer for TEOF.\n"\
        f"Task ID: {task.get('id')}\n"
        f"Title: {task.get('title')}\n"
        f"Plan: {plan}\n\n"
        f"Notes: {notes}\n\n"
        "Guardrails: \n"
        f"- Diff limit: {guardrails.get('diff_limit')} lines\n"
        f"- Tests: {', '.join(guardrails.get('tests', [])) or 'none'}\n"
        f"- Receipts directory: {guardrails.get('receipts_dir')}\n\n"
        "Respond in JSON with keys `analysis`, `commands`, `receipts`."
    )


def _write_receipt(payload: Mapping[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"conductor-{payload['generated_at'].replace(':', '').replace('-', '')}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _load_json(path: Path) -> Mapping[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
    if isinstance(data, Mapping):
        return data
    return None


def build_cycle_payload(
    *,
    task: Mapping[str, Any],
    guardrails: Mapping[str, Any],
    preflight: Mapping[str, Any],
    frontier_preview: list[Dict[str, Any]] | None = None,
    critic_alerts: list[Dict[str, Any]] | None = None,
    tms_conflicts: list[Dict[str, Any]] | None = None,
    objectives_snapshot: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "generated_at": _iso_now(),
        "task": task,
        "guardrails": guardrails,
        "prompt": _format_prompt(task, guardrails),
        "preflight": preflight,
        "frontier_preview": frontier_preview or [],
        "critic_alerts": critic_alerts or [],
        "tms_conflicts": tms_conflicts or [],
        "objectives_snapshot": objectives_snapshot or {},
    }


def run_once(
    *,
    diff_limit: int,
    tests: list[str],
    receipts_subdir: str,
    plan_id: str | None,
    dry_run: bool,
) -> tuple[bool, Dict[str, Any] | None, Path | None]:
    selection = next_step.select_next_step(claim=True)
    if selection is None:
        return False, None, None
    if plan_id and selection.get("id") != plan_id:
        # revert claim when the selected task does not match
        next_step._update_completion(  # type: ignore[attr-defined]
            item_id=str(selection.get("id")), status="pending"
        )
        return False, None, None

    guardrails = {
        "diff_limit": diff_limit,
        "tests": tests,
        "receipts_dir": receipts_subdir,
    }

    snapshot = preflight_mod.gather_snapshot(frontier_limit=5)
    frontier_preview = snapshot.get("frontier_preview", [])
    critic_alerts = [
        alert
        for alert in snapshot.get("critic_alerts", [])
        if isinstance(alert, Mapping) and alert.get("id") == selection.get("id")
    ]
    tms_conflicts = [
        conflict
        for conflict in snapshot.get("tms_conflicts", [])
        if isinstance(conflict, Mapping) and conflict.get("id") == selection.get("id")
    ]
    ethics_violations = [
        violation
        for violation in snapshot.get("ethics_violations", [])
        if isinstance(violation, Mapping) and violation.get("id") == selection.get("id")
    ]

    if ethics_violations:
        next_step._update_completion(  # type: ignore[attr-defined]
            item_id=str(selection.get("id")), status="pending"
        )
        print(
            "conductor: ethics gate blocked task"
            f" {selection.get('id')} — add consent/review receipts before rerunning."
        )
        return False, None, None

    preflight = {
        "authenticity": snapshot.get("authenticity"),
        "planner_status": snapshot.get("planner_status"),
    }
    payload = build_cycle_payload(
        task=selection,
        guardrails=guardrails,
        preflight=preflight,
        frontier_preview=frontier_preview[:3] if isinstance(frontier_preview, list) else [],
        critic_alerts=critic_alerts,
        tms_conflicts=tms_conflicts,
        objectives_snapshot=snapshot.get("objectives") or objectives_status.compute_status(window_days=7.0),
    )
    receipt_path = _write_receipt(payload)
    print(f"conductor: wrote {receipt_path.relative_to(ROOT)}")

    if dry_run:
        # reset the claim so that another agent can pick the task up later
        next_step._update_completion(  # type: ignore[attr-defined]
            item_id=str(selection.get("id")), status="pending"
        )
        return True, payload, receipt_path

    print("conductor: execute the commands suggested in the prompt using your preferred tool.")
    return True, payload, receipt_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diff-limit", type=int, default=200, help="Maximum diff lines per cycle")
    parser.add_argument(
        "--test", dest="tests", action="append", default=["pytest"], help="Tests to run (repeatable)"
    )
    parser.add_argument(
        "--receipts-dir",
        default="_report/usage/autonomy-conductor",
        help="Relative directory for receipts produced by the agent",
    )
    parser.add_argument("--plan-id", help="Process only the specified plan id")
    parser.add_argument("--dry-run", action="store_true", help="Generate prompt but leave task pending")
    parser.add_argument("--watch", action="store_true", help="Keep polling when no tasks are pending")
    parser.add_argument("--sleep", type=float, default=60.0, help="Seconds between watch cycles")
    parser.add_argument("--max-iterations", type=int, default=1, help="Maximum cycles per run (0 = infinite)")
    parser.add_argument(
        "--emit-prompt",
        action="store_true",
        help="Print the generated prompt to stdout after writing the receipt",
    )
    parser.add_argument(
        "--emit-json",
        action="store_true",
        help="Print the generated receipt payload JSON to stdout",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    iterations = 0
    limit = args.max_iterations if args.max_iterations > 0 else None

    while True:
        processed, payload, receipt_path = run_once(
            diff_limit=args.diff_limit,
            tests=args.tests,
            receipts_subdir=args.receipts_dir,
            plan_id=args.plan_id,
            dry_run=args.dry_run,
        )
        should_continue = False

        if processed:
            if args.emit_json and payload is not None:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            if args.emit_prompt and payload is not None:
                print(payload.get("prompt", ""))
            iterations += 1
            if limit is None or iterations < limit:
                should_continue = args.watch
        else:
            if args.watch:
                should_continue = True
            else:
                break

        if not should_continue:
            break

        time.sleep(max(args.sleep, 0.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
def _write_response(response: Mapping[str, Any]) -> Path:
    RESPONSE_DIR.mkdir(parents=True, exist_ok=True)
    ts = _iso_now().replace(":", "").replace("-", "")
    path = RESPONSE_DIR / f"response-{ts}.json"
    path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
