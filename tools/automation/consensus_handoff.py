#!/usr/bin/env python3
"""Record consensus handoff receipts when direct bus access is unavailable."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from teof._paths import repo_root

ROOT = repo_root(default=Path(__file__).resolve().parents[2])


def _utc_now() -> dt.datetime:
    return dt.datetime.utcnow().replace(microsecond=0)


def _iso_timestamp(when: dt.datetime | None = None) -> str:
    return (when or _utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp_token(when: dt.datetime | None = None) -> str:
    return (when or _utc_now()).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _handoff_dir(root: Path) -> Path:
    return root / "_report" / "analysis" / "consensus-handoff"


def run(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    handoff_dir = _handoff_dir(root)
    pointer_path = handoff_dir / "latest.json"
    now = _utc_now()
    stamp = _stamp_token(now)
    receipt_path = handoff_dir / f"handoff-{stamp}.json"
    payload: dict[str, Any] = {
        "schema": "consensus.handoff/1",
        "generated_at": _iso_timestamp(now),
        "agent_id": args.agent_id,
        "requestor": args.requestor,
        "pending_action": args.pending_action,
        "reason": args.reason,
        "plan_id": args.plan_id,
        "branch": args.branch,
        "details": args.details,
        "requires_push": bool(args.requires_push),
        "next_steps": args.next_steps,
    }
    _write_json(receipt_path, payload)
    pointer_payload = {
        "generated_at": payload["generated_at"],
        "receipt": _relative(receipt_path),
        "pending_action": payload["pending_action"],
        "requires_push": payload["requires_push"],
        "agent_id": payload["agent_id"],
    }
    _write_json(pointer_path, pointer_payload)
    print(f"handoff recorded → {_relative(receipt_path)}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-id", default="unknown", help="Agent logging the handoff (default: unknown)")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repo root (default: auto-detect)")
    parser.add_argument("--requestor", help="Person/system requesting consensus")
    parser.add_argument(
        "--pending-action",
        required=True,
        help="Summary of the action awaiting consensus (e.g., 'Push branch feature/foo')",
    )
    parser.add_argument(
        "--reason",
        required=True,
        help="Why consensus cannot be completed (e.g., 'no bus access from sandbox')",
    )
    parser.add_argument("--plan-id", help="Associated plan id if applicable")
    parser.add_argument("--branch", help="Git branch containing the pending work")
    parser.add_argument("--details", help="Free-form details for the reviewing agent")
    parser.add_argument(
        "--next-steps",
        help="Concrete follow-up instructions for the next agent",
        default="Review receipt and proceed via bus/consensus workflow.",
    )
    parser.add_argument(
        "--requires-push",
        action="store_true",
        help="Flag when the next action is to push to main after consensus",
    )
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
