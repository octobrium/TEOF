"""Shared helpers for emitting bus claims from automation modules."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from teof._paths import repo_root

from tools.autonomy.shared import atomic_write_json

ROOT = repo_root(default=Path(__file__).resolve().parents[2])
CLAIMS_DIR = Path("_bus") / "claims"


def _claims_dir(root: Path) -> Path:
    path = root / CLAIMS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _relative(path: Path, root: Path) -> str:
    path = path.resolve()
    root = root.resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _slugify(value: str) -> str:
    text = value.strip().replace(" ", "-")
    allowed = []
    for ch in text:
        if ch.isalnum() or ch in {"-", "_"}:
            allowed.append(ch)
        else:
            allowed.append("-")
    slug = "".join(allowed).strip("-_") or "task"
    return slug


def emit_claim(
    task_id: str,
    *,
    agent_id: str,
    note: str | None,
    plan_id: str | None,
    receipt_path: Path,
    branch: str | None = None,
    status: str = "pending",
    root: Path | None = None,
    extra_fields: Mapping[str, Any] | None = None,
    replace: bool = False,
) -> Path:
    base = root.resolve() if root is not None else ROOT
    claims_dir = _claims_dir(base)
    normalized = _slugify(task_id)
    claim_path = claims_dir / f"{normalized}.json"
    if claim_path.exists() and not replace:
        return claim_path
    payload: dict[str, Any] = {
        "task_id": normalized,
        "status": status,
        "agent_id": agent_id,
        "plan_id": plan_id,
        "branch": branch or f"agent/{agent_id}/{normalized.lower()}",
        "note": note,
        "receipt": _relative(receipt_path, base),
    }
    if extra_fields:
        payload.update(extra_fields)
    atomic_write_json(claim_path, payload)
    return claim_path


__all__ = ["emit_claim"]
