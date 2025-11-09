"""Shared coordination service primitives for autonomy modules."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping, Tuple

from tools.autonomy.shared import load_json


DEFAULT_ROOT = Path(__file__).resolve().parents[3]
_PENDING_STATUSES = {"pending", "queued", "in_progress"}


class CoordinationServiceError(RuntimeError):
    """Raised when coordination helpers cannot satisfy a request."""


@dataclass
class CoordinationService:
    """Provide consolidated helpers for autonomy coordination flows."""

    root: Path = DEFAULT_ROOT
    todo_path: Path | None = None
    plans_dir: Path | None = None

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        if self.todo_path is None:
            self.todo_path = self.root / "_plans" / "next-development.todo.json"
        if self.plans_dir is None:
            self.plans_dir = self.root / "_plans"

    # ------------------------------------------------------------------ loaders
    def load_todo(self) -> Dict[str, Any]:
        payload = load_json(self.todo_path) if self.todo_path else None
        if not isinstance(payload, dict):
            raise CoordinationServiceError("::error:: next-development.todo.json missing or invalid")
        return payload

    def load_plan(self, plan_id: str) -> Dict[str, Any]:
        if not plan_id:
            raise CoordinationServiceError("::error:: plan id missing")
        path = (self.plans_dir or self.root / "_plans") / f"{plan_id}.plan.json"
        payload = load_json(path)
        if not isinstance(payload, dict):
            raise CoordinationServiceError(f"::error:: plan {plan_id} not found or invalid")
        payload.setdefault("plan_id", plan_id)
        return payload

    # ------------------------------------------------------------------ helpers
    def iter_backlog_candidates(self, todo: Mapping[str, Any]) -> Iterator[dict]:
        items = todo.get("items")
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "").lower()
            if status in _PENDING_STATUSES:
                yield item

    @staticmethod
    def _step_status(step: Mapping[str, Any]) -> str:
        status = step.get("status")
        return str(status or "").lower()

    def first_pending_step(self, plan: Mapping[str, Any]) -> Dict[str, Any]:
        steps = plan.get("steps")
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict):
                    continue
                if self._step_status(step) == "done":
                    continue
                return step
        plan_id = plan.get("plan_id", "unknown")
        raise CoordinationServiceError(f"::error:: plan {plan_id} has no pending steps")

    def select_step(self, plan: Mapping[str, Any], step_id: str) -> Dict[str, Any]:
        steps = plan.get("steps")
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict):
                    continue
                if step.get("id") == step_id:
                    return step
        plan_id = plan.get("plan_id", "unknown")
        raise CoordinationServiceError(f"::error:: step {step_id} not found in plan {plan_id}")

    # ------------------------------------------------------------------ orchestration
    def select_work(self) -> Tuple[dict, Dict[str, Any], Dict[str, Any]]:
        """Return the next backlog item with an actionable plan step."""

        todo = self.load_todo()
        for item in self.iter_backlog_candidates(todo):
            plan_id = item.get("plan_suggestion")
            if not isinstance(plan_id, str) or not plan_id:
                continue
            try:
                plan = self.load_plan(plan_id)
            except CoordinationServiceError:
                continue
            try:
                step = self.first_pending_step(plan)
            except CoordinationServiceError:
                continue
            return item, plan, step
        raise CoordinationServiceError("::error:: no pending todo items with actionable plans")


__all__ = ["CoordinationService", "CoordinationServiceError"]
