#!/usr/bin/env python3
"""Helpers for creating receipt skeletons."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = ROOT / "_report" / "agent"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_FILES = ("notes.md", "actions.json", "tests.json", "summary.json")


class ScaffoldError(RuntimeError):
    """Raised when scaffolding cannot be completed."""


@dataclass
class ScaffoldResult:
    created: list[Path]


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _ensure_agent(agent: str) -> str:
    cleaned = (agent or "").strip()
    if not cleaned:
        raise ScaffoldError("agent id is required for scaffolding")
    return cleaned


def _base_dir(agent: str, slug: str | None) -> Path:
    agent_id = _ensure_agent(agent)
    folder = (slug or "").strip() or "untitled"
    return REPORT_ROOT / agent_id / folder


def _write_text(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _write_json(path: Path, payload: dict) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_to_json(payload), encoding="utf-8")
    return True


def _to_json(payload: dict) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _default_notes(plan_id: str) -> str:
    return (
        f"# Notes for {plan_id}\n\n"
        "- [ ] Outline verification steps for each plan milestone.\n"
        "- [ ] Record blockers, decisions, and handoffs.\n"
    )


def _default_actions(plan_id: str) -> dict:
    return {
        "plan_id": plan_id,
        "generated_at": _iso_now(),
        "actions": [],
    }


def _default_tests(plan_id: str) -> dict:
    return {
        "plan_id": plan_id,
        "generated_at": _iso_now(),
        "tests": [],
    }


def _default_summary(plan_id: str) -> dict:
    return {
        "plan_id": plan_id,
        "generated_at": _iso_now(),
        "status": "pending",
        "highlights": [],
        "blockers": [],
    }


def _default_design(plan_id: str) -> str:
    timestamp = _iso_now()
    return (
        f"# Design log for {plan_id}\n\n"
        f"Generated {timestamp}. Replace this placeholder with design notes.\n"
    )


def _claim_metadata(task_id: str, agent: str, plan_id: str | None, branch: str | None) -> dict:
    payload = {
        "task_id": task_id,
        "agent": agent,
        "generated_at": _iso_now(),
    }
    if plan_id:
        payload["plan_id"] = plan_id
    if branch:
        payload["branch"] = branch
    return payload


def scaffold_plan(
    plan_id: str,
    *,
    agent: str,
    include_design: bool = False,
    slug: str | None = None,
) -> ScaffoldResult:
    """Create receipt skeleton files for a plan."""

    if not isinstance(plan_id, str) or not plan_id.strip():
        raise ScaffoldError("plan_id must be a non-empty string")

    target_dir = _base_dir(agent, slug or plan_id)
    created: list[Path] = []

    for name in DEFAULT_FILES:
        path = target_dir / name
        if name.endswith(".md"):
            if _write_text(path, _default_notes(plan_id)):
                created.append(path)
        elif name == "actions.json":
            if _write_json(path, _default_actions(plan_id)):
                created.append(path)
        elif name == "tests.json":
            if _write_json(path, _default_tests(plan_id)):
                created.append(path)
        elif name == "summary.json":
            if _write_json(path, _default_summary(plan_id)):
                created.append(path)

    if include_design:
        design_path = target_dir / "design.md"
        if _write_text(design_path, _default_design(plan_id)):
            created.append(design_path)

    return ScaffoldResult(created=created)


def scaffold_claim(
    *,
    task_id: str,
    agent: str,
    plan_id: str | None = None,
    branch: str | None = None,
    slug: str | None = None,
    include_design: bool = False,
) -> ScaffoldResult:
    """Create receipt skeleton files tied to a claim/task."""

    if not isinstance(task_id, str) or not task_id.strip():
        raise ScaffoldError("task_id must be a non-empty string")

    base_slug = slug or plan_id or task_id.lower()
    plan_result = scaffold_plan(plan_id or task_id.lower(), agent=agent, include_design=include_design, slug=base_slug)
    claim_path = _base_dir(agent, base_slug) / "claim.json"
    created = list(plan_result.created)
    if _write_json(claim_path, _claim_metadata(task_id, agent, plan_id, branch)):
        created.append(claim_path)
    return ScaffoldResult(created=created)


def format_created(paths: Sequence[Path]) -> str:
    if not paths:
        return "No new files created (existing scaffold is intact)."
    parts: list[str] = []
    for path in paths:
        try:
            parts.append(path.relative_to(ROOT).as_posix())
        except ValueError:
            parts.append(path.as_posix())
    joined = "\n".join(f"  - {p}" for p in parts)
    return f"Created:\n{joined}"


__all__ = [
    "ScaffoldError",
    "ScaffoldResult",
    "scaffold_plan",
    "scaffold_claim",
    "format_created",
]
