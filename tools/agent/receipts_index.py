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

from tools.autonomy.shared import write_receipt_payload

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


@dataclass
class IndexPayload:
    summary: Dict[str, Any]
    plans: List[Dict[str, Any]]
    receipts: List[Dict[str, Any]]
    manager_messages: List[Dict[str, Any]]


@dataclass
class IndexWriteResult:
    mode: str  # "stdout" | "file" | "directory"
    paths: List[Path]


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
            mtime_iso: Optional[str] = None
            if exists:
                try:
                    stat = target.stat()
                except OSError:
                    stat = None
                else:
                    mtime_iso = _iso_timestamp(stat.st_mtime)
            refs.setdefault(rel, []).append(ReceiptReference(plan_id=plan_id, level="plan", step_id=None))
            plan_receipts.append(
                {
                    "path": rel,
                    "exists": exists,
                    "tracked": tracked_flag,
                    "mtime": mtime_iso,
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
                mtime_iso: Optional[str] = None
                if exists:
                    try:
                        stat = target.stat()
                    except OSError:
                        stat = None
                    else:
                        mtime_iso = _iso_timestamp(stat.st_mtime)
                refs.setdefault(rel, []).append(ReceiptReference(plan_id=plan_id, level="step", step_id=step_id))
                step_receipts.append(
                    {
                        "path": rel,
                        "exists": exists,
                        "tracked": tracked_flag,
                        "mtime": mtime_iso,
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
    payload = build_index_payload(root, tracked=tracked)
    return [payload.summary, *payload.plans, *payload.receipts, *payload.manager_messages]


def build_index_payload(root: Path, *, tracked: Optional[set[str]]) -> IndexPayload:
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

    return IndexPayload(
        summary=summary,
        plans=plans,
        receipts=receipts,
        manager_messages=manager_messages,
    )


def _write_chunks(
    entries: List[Dict[str, Any]],
    *,
    base_dir: Path,
    subdir: str,
    prefix: str,
    chunk_size: int,
) -> List[Path]:
    target_dir = base_dir / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    if not entries:
        path = target_dir / f"{prefix}-0001.jsonl"
        path.write_text("", encoding="utf-8")
        return [path.relative_to(base_dir)]

    paths: List[Path] = []
    for index, start in enumerate(range(0, len(entries), chunk_size), start=1):
        chunk = entries[start : start + chunk_size]
        path = target_dir / f"{prefix}-{index:04d}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for entry in chunk:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        paths.append(path.relative_to(base_dir))
    return paths


def write_index(
    payload: IndexPayload,
    output: Path | None,
    *,
    chunk_size: int = 500,
) -> IndexWriteResult:
    if output is None:
        try:
            print(json.dumps(payload.summary, ensure_ascii=False))
            for entry in payload.plans:
                print(json.dumps(entry, ensure_ascii=False))
            for entry in payload.receipts:
                print(json.dumps(entry, ensure_ascii=False))
            for entry in payload.manager_messages:
                print(json.dumps(entry, ensure_ascii=False))
        except BrokenPipeError:
            # Downstream consumer (e.g., head) closed early; suppress noisy traceback.
            try:
                sys.stdout.close()
            except Exception:
                pass
            os._exit(0)
        return IndexWriteResult(mode="stdout", paths=[])

    if output.suffix:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload.summary, ensure_ascii=False) + "\n")
            for entry in payload.plans:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            for entry in payload.receipts:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            for entry in payload.manager_messages:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return IndexWriteResult(mode="file", paths=[output])

    out_dir = output
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(payload.summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    plans_paths = _write_chunks(payload.plans, base_dir=out_dir, subdir="plans", prefix="plans", chunk_size=chunk_size)
    receipts_paths = _write_chunks(
        payload.receipts,
        base_dir=out_dir,
        subdir="receipts",
        prefix="receipts",
        chunk_size=chunk_size,
    )
    manager_paths = _write_chunks(
        payload.manager_messages,
        base_dir=out_dir,
        subdir="manager",
        prefix="manager",
        chunk_size=chunk_size,
    )

    manifest = {
        "summary": payload.summary,
        "chunk_size": chunk_size,
        "paths": {
            "summary": "summary.json",
            "plans": [path.as_posix() for path in plans_paths],
            "receipts": [path.as_posix() for path in receipts_paths],
            "manager_messages": [path.as_posix() for path in manager_paths],
        },
    }
    manifest_path = out_dir / "manifest.json"
    write_receipt_payload(manifest_path, manifest)

    absolute_paths = [
        manifest_path,
        summary_path,
        *[out_dir / path for path in plans_paths],
        *[out_dir / path for path in receipts_paths],
        *[out_dir / path for path in manager_paths],
    ]
    return IndexWriteResult(mode="directory", paths=absolute_paths)


def load_index_from_manifest(manifest_path: Path) -> IndexPayload:
    manifest_dir = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary = manifest.get("summary") or {}

    def _read_chunks(rel_paths: Iterable[str]) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        for rel in rel_paths:
            path = manifest_dir / rel
            if not path.exists():
                continue
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries

    paths_section = manifest.get("paths") or {}
    plans = _read_chunks(paths_section.get("plans") or [])
    receipts = _read_chunks(paths_section.get("receipts") or [])
    manager = _read_chunks(paths_section.get("manager_messages") or [])
    return IndexPayload(
        summary=summary,
        plans=plans,
        receipts=receipts,
        manager_messages=manager,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        help="Write JSONL output to this path (relative paths land under _report/usage/)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Number of records per chunk when writing to a directory (default: 500)",
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
    payload = build_index_payload(root, tracked=tracked)
    output_path = resolve_output(args.output, root=root)
    result = write_index(payload, output_path, chunk_size=max(1, args.chunk_size))
    if result.mode == "file":
        target = result.paths[0]
        message_path = target.relative_to(root) if target.is_relative_to(root) else target
        print(f"wrote index to {message_path}")
    elif result.mode == "directory":
        manifest = result.paths[0]
        message_path = manifest.relative_to(root) if manifest.is_relative_to(root) else manifest
        print(f"wrote index manifest to {message_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
