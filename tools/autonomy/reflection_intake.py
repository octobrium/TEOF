"""Capture personal reflections and emit structured intake records."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

VALID_LAYERS = {f"L{i}" for i in range(0, 7)}

ROOT = Path(__file__).resolve().parents[2]
REFLECTION_DIR = ROOT / "memory" / "reflections"
BACKLOG_SNIPPETS_DIR = ROOT / "_report" / "usage" / "reflection-intake"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Short name for the reflection")
    parser.add_argument(
        "--layer",
        action="append",
        dest="layers",
        required=True,
        help="Layer tag (L0-L6). Repeat for multiple layers.",
    )
    parser.add_argument("--summary", required=True, help="Core observation in plain text")
    parser.add_argument("--signals", help="Signals or evidence motivating the reflection")
    parser.add_argument(
        "--actions",
        help="Optional follow-up actions or backlog hints derived from the reflection",
    )
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        default=[],
        help="Optional tag (repeatable) for later filtering",
    )
    parser.add_argument(
        "--plan-suggestion",
        help="Optional plan id if the reflection should seed a specific roadmap",
    )
    parser.add_argument(
        "--notes",
        help="Supplementary free-form notes (kept in the record but not surfaced in backlog snippets)",
    )
    parser.add_argument(
        "--emit-backlog",
        action="store_true",
        help="Print a backlog item suggestion JSON to stdout",
    )
    parser.add_argument(
        "--backlog-out",
        type=Path,
        help="Optional path to write the backlog suggestion JSON",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root (for testing). Defaults to the module location",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render output to stdout without writing files",
    )
    return parser


def _validate_layers(layers: List[str]) -> List[str]:
    normalised: List[str] = []
    for layer in layers:
        layer_id = layer.strip().upper()
        if layer_id not in VALID_LAYERS:
            raise SystemExit(f"invalid layer '{layer}'; expected one of {sorted(VALID_LAYERS)}")
        normalised.append(layer_id)
    return normalised


def _make_record(args: argparse.Namespace, *, rel_path: str) -> Dict[str, object]:
    return {
        "captured_at": _iso_now(),
        "title": args.title,
        "layers": args.layers,
        "summary": args.summary,
        "signals": args.signals,
        "actions": args.actions,
        "tags": args.tags,
        "plan_suggestion": args.plan_suggestion,
        "notes": args.notes,
        "receipt": rel_path,
    }


def _backlog_payload(args: argparse.Namespace, *, receipt_rel_path: str) -> Dict[str, object]:
    notes = args.summary
    if args.actions:
        notes = f"{notes}\n\nFollow-ups: {args.actions}"
    return {
        "title": args.title,
        "status": "pending",
        "plan_suggestion": args.plan_suggestion or "",
        "notes": notes,
        "layer": args.layers[0],
        "source": f"reflection-intake:{receipt_rel_path}",
        "tags": args.tags,
    }


def main(argv: List[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    root = args.root.resolve()
    args.layers = _validate_layers(args.layers)

    reflection_dir = root / REFLECTION_DIR.relative_to(ROOT)
    backlog_dir = root / BACKLOG_SNIPPETS_DIR.relative_to(ROOT)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reflection_filename = f"reflection-{timestamp}.json"
    reflection_path = reflection_dir / reflection_filename
    receipt_rel = reflection_path.relative_to(root)

    record = _make_record(args, rel_path=str(receipt_rel))

    if args.dry_run:
        print(json.dumps(record, ensure_ascii=False, indent=2))
    else:
        reflection_dir.mkdir(parents=True, exist_ok=True)
        reflection_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"reflection: wrote {receipt_rel}")

    if args.emit_backlog or args.backlog_out:
        backlog_payload = _backlog_payload(args, receipt_rel_path=str(receipt_rel))
        if args.emit_backlog:
            print(json.dumps(backlog_payload, ensure_ascii=False, indent=2))
        if args.backlog_out:
            backlog_dir.mkdir(parents=True, exist_ok=True)
            args.backlog_out.write_text(json.dumps(backlog_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"reflection: backlog suggestion -> {args.backlog_out.relative_to(root)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
