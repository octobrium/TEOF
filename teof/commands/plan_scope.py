from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from teof._paths import repo_root
from tools.autonomy import receipt_utils
from tools.autonomy.shared import load_task_items, utc_timestamp


ROOT = repo_root(default=Path(__file__).resolve().parents[2])
PLANS_DIR = ROOT / "_plans"
TASKS_PATH = ROOT / "agents" / "tasks" / "tasks.json"
CLAIMS_DIR = ROOT / "_bus" / "claims"
ASSIGNMENTS_DIR = ROOT / "_bus" / "assignments"
MESSAGES_DIR = ROOT / "_bus" / "messages"


@dataclass
class ScopedFile:
    path: Path
    source: str

    def as_dict(self) -> dict[str, str | bool]:
        rel = self.path.relative_to(ROOT) if self.path.is_absolute() else self.path
        resolved = ROOT / rel
        return {
            "path": rel.as_posix(),
            "exists": resolved.exists(),
            "source": self.source,
        }


def _plan_path(plan_id: str) -> Path:
    path = PLANS_DIR / f"{plan_id}.plan.json"
    if not path.exists():
        raise SystemExit(f"plan '{plan_id}' not found at {path.relative_to(ROOT)}")
    return path


def _collect_receipts(plan_id: str) -> list[str]:
    try:
        return receipt_utils.collect_plan_receipts(plan_id, plans_dir=PLANS_DIR)
    except FileNotFoundError as exc:  # pragma: no cover - validated earlier
        raise SystemExit(str(exc)) from exc


def _collect_task_files(plan_id: str) -> list[ScopedFile]:
    tasks = load_task_items(TASKS_PATH)
    scoped: list[ScopedFile] = []
    for task in tasks:
        if task.get("plan_id") != plan_id:
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str):
            continue
        for directory, label in (
            (CLAIMS_DIR, "task_claim"),
            (ASSIGNMENTS_DIR, "task_assignment"),
        ):
            path = directory / f"{task_id}.json"
            scoped.append(ScopedFile(path=path, source=label))
        msg_path = (MESSAGES_DIR / f"{task_id}.jsonl")
        scoped.append(ScopedFile(path=msg_path, source="task_messages"))
    return scoped


def _collect_files(plan_id: str) -> list[ScopedFile]:
    scoped: list[ScopedFile] = []
    plan_file = _plan_path(plan_id)
    scoped.append(ScopedFile(path=plan_file, source="plan"))
    receipts = _collect_receipts(plan_id)
    for receipt in receipts:
        receipt_path = Path(receipt)
        if not receipt_path.is_absolute():
            receipt_path = ROOT / receipt_path
        scoped.append(ScopedFile(path=receipt_path, source="receipt"))
    scoped.extend(_collect_task_files(plan_id))
    unique: dict[str, ScopedFile] = {}
    for entry in scoped:
        rel = entry.as_dict()["path"]
        unique[rel] = entry
    return list(unique.values())


def _render_table(entries: Iterable[ScopedFile]) -> str:
    rows: list[list[str]] = []
    for entry in entries:
        payload = entry.as_dict()
        rows.append(
            [
                payload["path"],  # type: ignore[index]
                "yes" if payload["exists"] else "no",  # type: ignore[index]
                payload["source"],  # type: ignore[index]
            ]
        )
    headers = ["path", "exists", "source"]
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    fmt = " ".join(f"{{:<{w}}}" for w in widths)
    lines = [fmt.format(*headers)]
    lines.append("-" * (sum(widths) + len(widths) - 1))
    for row in rows:
        lines.append(fmt.format(*row))
    if not rows:
        lines.append("(no files)")
    return "\n".join(lines)


def _write_manifest(path: Path, plan_id: str, files: list[ScopedFile]) -> Path:
    payload = {
        "plan_id": plan_id,
        "generated_at": utc_timestamp(),
        "files": [entry.as_dict() for entry in files],
    }
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def run(args: argparse.Namespace) -> int:
    plan_id = getattr(args, "plan")
    if not plan_id:
        raise SystemExit("--plan is required")
    files = _collect_files(plan_id)
    manifest_path = getattr(args, "manifest", None)
    if manifest_path:
        manifest = _write_manifest(Path(manifest_path), plan_id, files)
        print(f"wrote manifest → {manifest.relative_to(ROOT)}")
    output_format = getattr(args, "format", "table")
    if output_format == "json":
        payload = {
            "plan_id": plan_id,
            "count": len(files),
            "files": [entry.as_dict() for entry in files],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_table(files))
    return 0


def register(subparsers: "argparse._SubParsersAction[object]") -> None:
    parser = subparsers.add_parser(
        "plan_scope",
        help="Inspect per-plan file scope to prepare incremental pushes",
    )
    parser.add_argument(
        "--plan",
        required=True,
        help="Plan identifier (e.g., 2025-11-09-plan-scope)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--manifest",
        help="Optional path to write a scope manifest JSON",
    )
    parser.set_defaults(func=run)


__all__ = ["register", "run"]
