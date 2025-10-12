"""Autonomous node workflow runner.

Executes core TEOF workflows (scan, status, idea evaluation) and writes
receipts under ``docs/usage/autonomous-node/<UTC>/``. Intended for
"mining" nodes that continuously expand TEOF with auditable outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from contextlib import redirect_stdout
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from teof.commands import scan as scan_cmd
from teof.commands import status as status_cmd
from teof.ideas import iter_ideas, evaluate_ideas

ROOT = Path(__file__).resolve().parents[2]
USAGE_ROOT = ROOT / "docs" / "usage" / "autonomous-node"


@dataclass
class NodeRunArtifacts:
    timestamp: str
    output_dir: Path
    status_path: Path
    scan_receipt_dir: Path
    scan_payload_path: Path
    ideas_payload_path: Path
    summary_path: Path


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _run_status(out_path: Path) -> None:
    args = argparse.Namespace(out=out_path, quiet=True)
    status_cmd.run(args)


def _run_scan(out_dir: Path, limit: int) -> str:
    scan_args = argparse.Namespace(
        limit=limit,
        format="json",
        out=out_dir,
        emit_bus=False,
        emit_plan=False,
        summary=False,
        only=None,
        skip=None,
    )
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        scan_cmd.run(scan_args)
    return buffer.getvalue()


def _write_scan_payload(out_dir: Path, payload_text: str) -> Path:
    path = out_dir / "scan.json"
    path.write_text(payload_text, encoding="utf-8")
    return path


def _run_ideas(include_promoted: bool, limit: int | None) -> list[dict[str, object]]:
    ideas = iter_ideas()
    if not include_promoted:
        ideas = [idea for idea in ideas if idea.status != "promoted"]
    scored = evaluate_ideas(ideas)
    if limit is not None and limit >= 0:
        scored = scored[: limit]
    return scored


def _materialise(out_dir: Path, ideas_payload: Iterable[dict[str, object]]) -> Path:
    path = out_dir / "ideas.json"
    _write_json(path, {"generated_at": _now().strftime("%Y-%m-%dT%H:%M:%SZ"), "ideas": list(ideas_payload)})
    return path


def _build_summary(artifacts: NodeRunArtifacts) -> None:
    summary = {
        "generated_at": artifacts.timestamp,
        "status": {
            "path": artifacts.status_path.relative_to(ROOT).as_posix(),
            "sha256": _sha256(artifacts.status_path),
        },
        "scan": {
            "out_dir": artifacts.scan_receipt_dir.relative_to(ROOT).as_posix(),
            "payload": artifacts.scan_payload_path.relative_to(ROOT).as_posix(),
            "sha256": _sha256(artifacts.scan_payload_path),
        },
        "ideas": {
            "path": artifacts.ideas_payload_path.relative_to(ROOT).as_posix(),
            "sha256": _sha256(artifacts.ideas_payload_path),
        },
    }
    _write_json(artifacts.summary_path, summary)


def run(limit: int = 10, include_promoted: bool = False, dest: Path | None = None) -> NodeRunArtifacts:
    timestamp = _now().strftime("%Y%m%dT%H%M%SZ")
    output_dir = (dest or USAGE_ROOT) / timestamp
    _ensure_dir(output_dir)

    status_path = output_dir / "status.md"
    _run_status(status_path)

    scan_receipt_dir = output_dir / "scan"
    _insure = scan_receipt_dir
    _ensure_dir(_insure)
    scan_payload_text = _run_scan(scan_receipt_dir, limit=limit)
    scan_payload_path = _write_scan_payload(scan_receipt_dir, scan_payload_text)

    ideas_payload = _run_ideas(include_promoted=include_promoted, limit=limit)
    ideas_payload_path = _materialise(output_dir, ideas_payload)

    summary_path = output_dir / "summary.json"
    artifacts = NodeRunArtifacts(
        timestamp=timestamp,
        output_dir=output_dir,
        status_path=status_path,
        scan_receipt_dir=scan_receipt_dir,
        scan_payload_path=scan_payload_path,
        ideas_payload_path=ideas_payload_path,
        summary_path=summary_path,
    )
    _build_summary(artifacts)
    return artifacts


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=10, help="Scan/idea evaluation limit (default: 10)")
    parser.add_argument("--include-promoted", action="store_true", help="Include promoted ideas in evaluation payload")
    parser.add_argument("--dest", type=Path, help="Override output directory (default: docs/usage/autonomous-node)")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    run(limit=args.limit, include_promoted=args.include_promoted, dest=args.dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
