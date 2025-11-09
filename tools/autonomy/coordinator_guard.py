"""Coordinator guardrail orchestrator.

Combines manifest generation, scan trigger checks, systemic evaluation,
and worker execution into a single guarded loop. This ensures donated
agent seats operate with the same observability and reversibility humans
expect while building the autonomous coordinator layer.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from tools.agent import session_guard, bus_event
from tools.autonomy import scan_trigger, coordinator_manager, coordinator_worker
from tools.autonomy.coord import CoordinationService, CoordinationServiceError
from tools.autonomy.shared import load_json, write_receipt_payload
from teof.eval import systemic_min


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "_report" / "agent"
DEFAULT_TASK_ID = "ND-067"


def _utc_now() -> str:
    import datetime as dt

    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _run_scan(label: str, *, force: bool = False) -> Dict[str, Any]:
    """Execute the alignment scan when tracked inputs changed."""

    report = scan_trigger.evaluate_trigger(root=ROOT, watch=scan_trigger.DEFAULT_WATCH)
    result: Dict[str, Any] = {
        "label": label,
        "triggered": report.triggered,
        "changed_paths": report.changed_paths,
        "exit_code": None,
    }
    if report.triggered or force:
        exit_code = scan_trigger.run_scan(summary=True)
        result["exit_code"] = exit_code
        result["status"] = "ok" if exit_code == 0 else "error"
    else:
        result["status"] = "skipped"
    return result


def _systemic_check(plan: Dict[str, Any], step: Dict[str, Any]) -> Dict[str, Any]:
    systemic_targets = ", ".join(plan.get("systemic_targets", [])) or "S1"
    layer_targets = ", ".join(plan.get("layer_targets", [])) or "L5"
    summary = str(plan.get("summary", ""))
    notes = str(step.get("notes", ""))
    coordinate = f"S{plan.get('systemic_scale', 6)}:{plan.get('layer_targets', ['L5'])[0]}"
    text = (
        f"# Task: {summary}\n"
        f"Systemic Targets: {systemic_targets}\n"
        f"Layer Targets: {layer_targets}\n"
        f"Goal: Execute {step.get('title', '')} under coordinator guardrails.\n"
        f"Coordinate: {coordinate}\n"
        f"Sunset: Pause automation if guardrail checks fail twice in succession.\n"
        f"Fallback: Manual operator reviews receipts and reruns guard.\n"
        f"Acceptance: {notes or 'Receipts captured, scan clean, systemic ready, bus note recorded.'}\n"
    )
    judgement = systemic_min.evaluate(text)
    result = {
        "text": text,
        "scores": judgement["scores"],
        "total": judgement["total"],
        "verdict": judgement["verdict"],
    }
    return result


def _load_manifest(agent_id: str, plan: Dict[str, Any], step: Dict[str, Any]) -> Path:
    manifest = coordinator_manager.build_manifest(agent_id=agent_id, plan=plan, step=step)
    manifest_path = coordinator_manager._manifest_output_path(agent_id)  # type: ignore[attr-defined]
    write_receipt_payload(manifest_path, manifest)
    return manifest_path


def _coord_service() -> CoordinationService:
    return CoordinationService(root=ROOT)


def _select_plan_and_step(
    *,
    plan_id: Optional[str],
    step_id: Optional[str],
    auto_select: bool,
) -> tuple[Dict[str, Any], Dict[str, Any], Optional[Dict[str, Any]]]:
    service = _coord_service()
    if auto_select or not plan_id:
        try:
            todo_item, plan, step = service.select_work()
        except CoordinationServiceError as exc:
            raise SystemExit(str(exc)) from exc
        return plan, step, todo_item

    try:
        plan = service.load_plan(plan_id)
    except CoordinationServiceError as exc:
        raise SystemExit(str(exc)) from exc

    if step_id:
        try:
            step = service.select_step(plan, step_id)
        except CoordinationServiceError as exc:
            raise SystemExit(str(exc)) from exc
    else:
        try:
            step = service.first_pending_step(plan)
        except CoordinationServiceError as exc:
            raise SystemExit(str(exc)) from exc
    return plan, step, None


def _log_bus(manager_agent: str, summary: str, status: str, task_id: str) -> None:
    payload = [
        "log",
        "--event",
        "status",
        "--task",
        task_id,
        "--summary",
        summary,
        "--severity",
        status,
    ]
    bus_event.main(payload)


def _state_path(manager_agent: str) -> Path:
    return STATE_PATH / manager_agent / "autonomy-coordinator" / "state.json"


def _update_state(path: Path, payload: Dict[str, Any]) -> Path:
    _ensure_dir(path)
    write_receipt_payload(path, payload)
    return path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", help="Plan id (without .plan.json suffix). Omit with --auto-select.")
    parser.add_argument("--step", help="Step id (defaults to first pending when --plan provided).")
    parser.add_argument("--manager-agent", help="Override manager agent id")
    parser.add_argument("--worker-agent", help="Worker agent id (default = manager)")
    parser.add_argument("--task-id", help="Task/backlog id for logging (defaults to ND-067 or auto-selected todo id)")
    parser.add_argument("--auto-select", action="store_true", help="Select work from `_plans/next-development.todo.json`")
    parser.add_argument("--execute", action="store_true", help="Execute the worker harness")
    parser.add_argument(
        "--allow-worker-stale",
        action="store_true",
        help="Allow worker session override (records guard)",
    )
    parser.add_argument("--no-bus", action="store_true", help="Skip logging guard status to manager-report")
    args = parser.parse_args(argv)

    if not args.plan and not args.auto_select:
        parser.error("provide --plan/--step or pass --auto-select to pick the next backlog item")
    if args.step and not args.plan:
        parser.error("--step requires --plan")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    manager_agent = session_guard.resolve_agent_id(args.manager_agent)
    session_guard.ensure_recent_session(manager_agent, context="coordinator_guard")

    plan, step, todo_item = _select_plan_and_step(
        plan_id=args.plan,
        step_id=args.step,
        auto_select=args.auto_select,
    )
    plan_id = str(plan.get("plan_id"))
    step_id = str(step.get("id"))
    task_id = args.task_id
    if not task_id:
        if todo_item and todo_item.get("id"):
            task_id = str(todo_item["id"])
        else:
            task_id = DEFAULT_TASK_ID
    manifest_path = _load_manifest(manager_agent, plan, step)
    manifest = load_json(manifest_path)

    systemic = _systemic_check(plan, step)
    circuit_reason = None

    if systemic.get("verdict") != "ready":
        circuit_reason = f"systemic_verdict={systemic.get('verdict')}"

    pre_scan = _run_scan("pre")
    if pre_scan.get("status") == "error" and circuit_reason is None:
        circuit_reason = "scan_pre_failed"

    worker_status = {
        "executed": False,
        "exit_code": None,
    }

    if args.execute and circuit_reason is None:
        worker_args = [str(manifest_path), "--execute"]
        if args.worker_agent:
            worker_args.extend(["--agent-id", args.worker_agent])
        if args.allow_worker_stale:
            worker_args.append("--allow-stale-session")
        exit_code = coordinator_worker.main(worker_args)
        worker_status.update({"executed": True, "exit_code": exit_code})
        if exit_code != 0 and circuit_reason is None:
            circuit_reason = f"worker_exit_{exit_code}"

    post_scan = _run_scan("post") if args.execute else {"label": "post", "status": "skipped", "triggered": False, "changed_paths": [], "exit_code": None}
    if post_scan.get("status") == "error" and circuit_reason is None:
        circuit_reason = "scan_post_failed"

    circuit_breaker = {
        "active": circuit_reason is not None,
        "reason": circuit_reason,
    }

    state_payload = {
        "version": 1,
        "generated_at": _utc_now(),
        "manager_agent": manager_agent,
        "plan_id": plan_id,
        "step_id": step_id,
        "task_id": task_id,
        "manifest_path": manifest_path.relative_to(ROOT).as_posix(),
        "systemic": systemic,
        "pre_scan": pre_scan,
        "post_scan": post_scan,
        "worker": worker_status,
        "circuit_breaker": circuit_breaker,
    }
    if todo_item:
        state_payload["todo_item"] = {
            "id": todo_item.get("id"),
            "title": todo_item.get("title"),
            "plan_suggestion": todo_item.get("plan_suggestion"),
            "status": todo_item.get("status"),
        }

    state_path = _state_path(manager_agent)
    _update_state(state_path, state_payload)

    summary = (
        f"Coordinator guard {plan_id}:{step_id}"
        f" manifest={manifest_path.name} systemic={systemic.get('verdict')}"
        f" circuit={'ON' if circuit_breaker['active'] else 'off'} task={task_id}"
    )
    if todo_item:
        summary += f" selection={todo_item.get('id')}"
    if not args.no_bus:
        severity = "high" if circuit_breaker["active"] else "low"
        try:
            _log_bus(manager_agent, summary, severity, task_id)
        except SystemExit:
            pass

    print(summary)
    if circuit_breaker["active"]:
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
