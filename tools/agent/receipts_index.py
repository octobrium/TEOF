#!/usr/bin/env python3
"""Build an index of receipts, plans, and manager messages."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = ROOT / "_plans"
REPORT_DIR = ROOT / "_report"
MANAGER_REPORT = ROOT / "_bus" / "messages" / "manager-report.jsonl"
DEFAULT_USAGE_DIR = REPORT_DIR / "usage"

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class ReceiptReference:
    plan_id: str
    level: str  # "plan" or "step"
    step_id: Optional[str]


def _iso_timestamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(ISO_FMT)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_tracked_paths(root: Path) -> Optional[set[str]]:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(root), "ls-files"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    entries = {line.strip() for line in output.splitlines() if line.strip()}
    return entries


def _plan_entries(root: Path, *, tracked: Optional[set[str]]) -> tuple[List[Dict[str, Any]], Dict[str, List[ReceiptReference]]]:
    entries: List[Dict[str, Any]] = []
    refs: Dict[str, List[ReceiptReference]] = {}

    if not PLANS_DIR.exists():
        return entries, refs

    for plan_path in sorted(PLANS_DIR.glob("*.plan.json")):
        data = _read_json(plan_path)
        plan_id = str(data.get("plan_id", plan_path.stem))
        receipts = data.get("receipts", []) or []
        plan_receipts: List[Dict[str, Any]] = []
        missing: List[str] = []

        for receipt in receipts:
            if not isinstance(receipt, str):
                continue
            rel = receipt.strip()
            target = root / rel
            exists = target.exists()
            tracked_flag = tracked is None or rel in tracked
            if not exists or not tracked_flag:
                missing.append(rel)
            refs.setdefault(rel, []).append(ReceiptReference(plan_id=plan_id, level="plan", step_id=None))
            plan_receipts.append(
                {
                    "path": rel,
                    "exists": exists,
                    "tracked": tracked_flag,
                }
            )

        step_entries: List[Dict[str, Any]] = []
        for step in data.get("steps", []) or []:
            step_id = str(step.get("id")) if step.get("id") else None
            step_receipts: List[Dict[str, Any]] = []
            for receipt in step.get("receipts", []) or []:
                if not isinstance(receipt, str):
                    continue
                rel = receipt.strip()
                target = root / rel
                exists = target.exists()
                tracked_flag = tracked is None or rel in tracked
                if not exists or not tracked_flag:
                    missing.append(rel)
                refs.setdefault(rel, []).append(ReceiptReference(plan_id=plan_id, level="step", step_id=step_id))
                step_receipts.append(
                    {
                        "path": rel,
                        "exists": exists,
                        "tracked": tracked_flag,
                    }
                )
            step_entries.append(
                {
                    "id": step_id,
                    "title": step.get("title"),
                    "status": step.get("status"),
                    "receipts": step_receipts,
                }
            )

        stat = plan_path.stat()
        entries.append(
            {
                "kind": "plan",
                "plan_id": plan_id,
                "path": plan_path.relative_to(root).as_posix(),
                "actor": data.get("actor"),
                "created": data.get("created"),
                "status": data.get("status"),
                "checkpoint_status": (data.get("checkpoint") or {}).get("status"),
                "updated": _iso_timestamp(stat.st_mtime),
                "receipts": plan_receipts,
                "steps": step_entries,
                "missing_receipts": sorted(set(missing)),
                "links": data.get("links", []),
            }
        )

    return entries, refs


def _category_for_receipt(rel_path: str) -> str | None:
    parts = rel_path.split("/")
    if len(parts) >= 2 and parts[0] == "_report":
        return parts[1]
    return None


def _receipt_entries(root: Path, *, tracked: Optional[set[str]], refs: Dict[str, List[ReceiptReference]]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    if not REPORT_DIR.exists():
        return entries

    for path in sorted(REPORT_DIR.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        stat = path.stat()
        entry_refs = [
            {
                "plan_id": ref.plan_id,
                "level": ref.level,
                "step_id": ref.step_id,
            }
            for ref in refs.get(rel, [])
        ]
        entries.append(
            {
                "kind": "receipt",
                "path": rel,
                "category": _category_for_receipt(rel),
                "size": stat.st_size,
                "mtime": _iso_timestamp(stat.st_mtime),
                "sha256": _hash_file(path),
                "tracked": (tracked is None) or (rel in tracked),
                "referenced_by": entry_refs,
            }
        )

    return entries


def _manager_entries(root: Path, *, tracked: Optional[set[str]]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    if not MANAGER_REPORT.exists():
        return entries
    rel_template = MANAGER_REPORT.relative_to(root).as_posix()
    with MANAGER_REPORT.open(encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            receipts_field = data.get("receipts") or []
            receipts_info: List[Dict[str, Any]] = []
            missing: List[str] = []
            for receipt in receipts_field:
                if not isinstance(receipt, str):
                    continue
                rel = receipt.strip()
                target = root / rel
                exists = target.exists()
                tracked_flag = (tracked is None) or (rel in tracked)
                if not exists or not tracked_flag:
                    missing.append(rel)
                receipts_info.append(
                    {
                        "path": rel,
                        "exists": exists,
                        "tracked": tracked_flag,
                    }
                )
            meta = data.get("meta") if isinstance(data.get("meta"), dict) else None
            plan_id = None
            if isinstance(meta, dict):
                value = meta.get("plan_id")
                if isinstance(value, str) and value.strip():
                    plan_id = value.strip()
            entries.append(
                {
                    "kind": "manager_message",
                    "path": rel_template,
                    "index": idx,
                    "timestamp": data.get("ts"),
                    "author": data.get("from"),
                    "message_type": data.get("type"),
                    "task_id": data.get("task_id"),
                    "plan_id": plan_id,
                    "summary": data.get("summary"),
                    "receipts": receipts_info,
                    "missing_receipts": missing,
                }
            )
    return entries


def build_index(root: Path, *, tracked: Optional[set[str]]) -> List[Dict[str, Any]]:
    plans, refs = _plan_entries(root, tracked=tracked)
    receipts = _receipt_entries(root, tracked=tracked, refs=refs)
    manager_messages = _manager_entries(root, tracked=tracked)

    summary = {
        "kind": "summary",
        "generated_at": datetime.utcnow().replace(tzinfo=timezone.utc).strftime(ISO_FMT),
        "counts": {
            "plans": len(plans),
            "receipts": len(receipts),
            "manager_messages": len(manager_messages),
        },
    }

    return [summary, *plans, *receipts, *manager_messages]


def write_index(entries: Iterable[Dict[str, Any]], output: Path | None) -> None:
    if output is None:
        try:
            for entry in entries:
                print(json.dumps(entry, ensure_ascii=False))
        except BrokenPipeError:
            # Downstream consumer (e.g., head) closed early; suppress noisy traceback.
            try:
                sys.stdout.close()
            except Exception:
                pass
            os._exit(0)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        help="Write JSONL output to this path (relative paths land under _report/usage/)",
    )
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help=argparse.SUPPRESS,
    )
    return parser


def resolve_output(path_str: Optional[str], *, root: Path) -> Path | None:
    if path_str is None:
        return None
    candidate = Path(path_str)
    if candidate.is_absolute():
        return candidate
    return (DEFAULT_USAGE_DIR / candidate).resolve()


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    tracked = _git_tracked_paths(root)
    entries = build_index(root, tracked=tracked)
    output_path = resolve_output(args.output, root=root)
    write_index(entries, output_path)
    if output_path is not None:
        print(f"wrote index to {output_path.relative_to(root) if output_path.is_relative_to(root) else output_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
