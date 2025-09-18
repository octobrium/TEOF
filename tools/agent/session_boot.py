#!/usr/bin/env python3
"""Session bootstrap helper for agents.

Logs a handshake event on the coordination bus and reports other active agents
and their claimed tasks so operators can coordinate without manual back-and-forth.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG = ROOT / "_bus" / "events" / "events.jsonl"
CLAIMS_DIR = ROOT / "_bus" / "claims"
MANIFEST_PATH = ROOT / "AGENT_MANIFEST.json"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_agent() -> str | None:
    if not MANIFEST_PATH.exists():
        return None
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    agent_id = data.get("agent_id")
    if isinstance(agent_id, str) and agent_id.strip():
        return agent_id.strip()
    return None


def _append_event(payload: dict[str, Any]) -> None:
    EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with EVENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _load_claims() -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    if not CLAIMS_DIR.exists():
        return claims
    for path in sorted(CLAIMS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        data["_path"] = path.relative_to(ROOT).as_posix()
        claims.append(data)
    return claims


def summarize_peers(claims: list[dict[str, Any]], self_agent: str) -> list[str]:
    peers: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        agent_id = claim.get("agent_id")
        status = claim.get("status")
        if agent_id and agent_id != self_agent and status in {"active", "paused"}:
            peers[agent_id].append(claim)
    summary: list[str] = []
    for agent_id, rows in sorted(peers.items()):
        tasks = ", ".join(f"{row.get('task_id')}[{row.get('status')}]=@{row.get('branch')}" for row in rows)
        summary.append(f"Peer {agent_id}: {tasks}")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap an agent session")
    parser.add_argument("--agent", help="Agent id (defaults to AGENT_MANIFEST.json)")
    parser.add_argument("--summary", default="Session handshake", help="Summary text for the handshake event")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    agent_id = args.agent or _default_agent()
    if not agent_id:
        parser.error("Agent id missing; provide --agent or populate AGENT_MANIFEST.json")

    payload = {
        "ts": _iso_now(),
        "agent_id": agent_id,
        "event": "handshake",
        "summary": args.summary,
        "branch_prefix": f"agent/{agent_id}/",
    }
    _append_event(payload)

    claims = _load_claims()
    summary_lines = summarize_peers(claims, agent_id)

    print(f"Recorded handshake for {agent_id} at {payload['ts']}")
    if summary_lines:
        print("Other active agents detected:")
        for line in summary_lines:
            print(f"  - {line}")
    else:
        print("No other active agents detected.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
