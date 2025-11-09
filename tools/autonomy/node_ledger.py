#!/usr/bin/env python3
"""Node incentive ledger CLI for ND-069."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable, List, Mapping


ROOT = Path(__file__).resolve().parents[2]
LEDGER_DIR = ROOT / "_report" / "usage" / "node-incentive-ledger"
LEDGER_PATH = LEDGER_DIR / "ledger.jsonl"
LATEST_PATH = LEDGER_DIR / "latest.json"
SCHEMA_PATH = ROOT / "schemas" / "node-incentive-ledger.schema.json"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
ACTION_CHOICES = ("grant", "reward", "penalty", "suspend")


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _ensure_paths(paths: Iterable[str]) -> List[str]:
    resolved: List[str] = []
    for entry in paths:
        candidate = Path(entry)
        if not candidate.is_absolute():
            candidate = (ROOT / candidate).resolve()
        if not candidate.exists():
            raise SystemExit(f"proof/authority path missing: {candidate}")
        try:
            resolved.append(candidate.relative_to(ROOT).as_posix())
        except ValueError:
            resolved.append(str(candidate))
    return resolved


def _read_entries(path: Path) -> List[dict]:
    if not path.exists():
        return []
    entries: List[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                entries.append(dict(payload))
    return entries


def _hash_entry(payload: Mapping[str, object]) -> str:
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return sha256(serialized.encode("utf-8")).hexdigest()


def _write_latest(entry: Mapping[str, object]) -> None:
    LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_PATH.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_entry(
    *,
    node_id: str,
    action: str,
    stake_delta: float,
    reputation_delta: float,
    authority: str,
    proofs: Iterable[str],
    notes: str | None,
    timestamp: str | None = None,
) -> dict:
    entries = _read_entries(LEDGER_PATH)
    last_hash = entries[-1].get("hash_self") if entries else ""
    resolved_authority = _ensure_paths([authority])[0]
    resolved_proofs = _ensure_paths(proofs)

    entry: dict[str, object] = {
        "ts": timestamp or _iso_now(),
        "node_id": node_id,
        "action": action,
        "stake_delta": stake_delta,
        "reputation_delta": reputation_delta,
        "authority": resolved_authority,
        "proofs": resolved_proofs,
        "hash_prev": last_hash,
    }
    if notes:
        entry["notes"] = notes
    entry["hash_self"] = _hash_entry(entry)

    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _write_latest(entry)
    return entry


def show_entries(*, node_id: str | None, limit: int) -> List[dict]:
    entries = _read_entries(LEDGER_PATH)
    if node_id:
        entries = [entry for entry in entries if entry.get("node_id") == node_id]
    entries = entries[-limit:] if limit > 0 else entries
    if not entries:
        print("(ledger empty)")
        return []
    header = f"{'ts':<20} {'node':<12} {'action':<8} stake rep authority"
    print(header)
    print("-" * len(header))
    for entry in entries:
        ts = entry.get("ts", "-")
        node = entry.get("node_id", "-")
        action = entry.get("action", "-")
        stake = entry.get("stake_delta", 0)
        rep = entry.get("reputation_delta", 0)
        authority = entry.get("authority", "-")
        print(f"{ts:<20} {node:<12} {action:<8} {stake:<5} {rep:<5} {authority}")
    return entries


def audit_entries() -> None:
    entries = _read_entries(LEDGER_PATH)
    previous_hash = ""
    for idx, entry in enumerate(entries):
        expected_prev = entry.get("hash_prev", "")
        if expected_prev != previous_hash:
            raise SystemExit(f"ledger audit failed at entry {idx}: hash_prev mismatch")
        computed = _hash_entry({k: entry[k] for k in entry if k != "hash_self"})
        if computed != entry.get("hash_self"):
            raise SystemExit(f"ledger audit failed at entry {idx}: hash mismatch")
        previous_hash = entry.get("hash_self", "")
    print(f"Ledger audit OK ({len(entries)} entries)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the node incentive ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    append_cmd = sub.add_parser("append", help="Append a ledger entry")
    append_cmd.add_argument("--node", required=True, help="Node identifier")
    append_cmd.add_argument("--action", required=True, choices=ACTION_CHOICES)
    append_cmd.add_argument("--stake", type=float, default=0.0, help="Stake delta")
    append_cmd.add_argument("--rep", type=float, default=0.0, help="Reputation delta")
    append_cmd.add_argument("--authority", required=True, help="Authoritative plan/anchor path")
    append_cmd.add_argument("--proof", action="append", required=True, help="Proof receipt path (repeatable)")
    append_cmd.add_argument("--note", help="Optional note")
    append_cmd.add_argument("--timestamp", help="Override ISO timestamp (UTC)")

    show_cmd = sub.add_parser("show", help="Show ledger entries")
    show_cmd.add_argument("--node", help="Filter by node id")
    show_cmd.add_argument("--limit", type=int, default=10, help="Number of entries to display")

    sub.add_parser("audit", help="Verify hash chain integrity")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "append":
        append_entry(
            node_id=args.node,
            action=args.action,
            stake_delta=args.stake,
            reputation_delta=args.rep,
            authority=args.authority,
            proofs=args.proof,
            notes=args.note,
            timestamp=args.timestamp,
        )
        print("Ledger entry appended.")
        return 0
    if args.command == "show":
        show_entries(node_id=args.node, limit=args.limit)
        return 0
    if args.command == "audit":
        audit_entries()
        return 0
    parser.error("unknown command")


if __name__ == "__main__":
    raise SystemExit(main())
