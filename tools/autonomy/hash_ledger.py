"""Hash-linked receipt ledger utilities."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

from teof._paths import repo_root
from tools.autonomy.shared import load_json

ROOT = repo_root()
LEDGER_DIR = ROOT / "_report" / "usage" / "hash-ledger"
INDEX_FILE = LEDGER_DIR / "index.jsonl"
STATE_FILE = LEDGER_DIR / "state.json"


def _ensure_ledger_dir() -> None:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)


def _canonical_payload(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _hash_payload(payload: Mapping[str, Any]) -> str:
    data = _canonical_payload(payload).encode("utf-8")
    return sha256(data).hexdigest()


def _load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"tip_hash": "0" * 64, "entry_count": 0}
    return load_json(STATE_FILE) or {"tip_hash": "0" * 64, "entry_count": 0}


def _write_state(state: Mapping[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _normalise_receipt_path(path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(ROOT)
        except ValueError as exc:  # pragma: no cover - guard for unexpected paths
            raise ValueError(f"receipt path must live under repo root ({ROOT})") from exc
    return candidate.as_posix()


def _load_metadata(source: Mapping[str, Any] | Path | None) -> Mapping[str, Any]:
    if source is None:
        return {}
    if isinstance(source, Mapping):
        return dict(source)
    data = load_json(source)
    return data if isinstance(data, Mapping) else {}


def _slug_timestamp(ts: str) -> str:
    allowed = []
    for ch in ts:
        if ch.isalnum():
            allowed.append(ch)
    slug = "".join(allowed)
    return slug or "ledger"


@dataclass
class LedgerEntry:
    version: int
    prev_hash: str
    plan_id: str
    plan_step_id: str | None
    receipt_path: str
    agent_id: str
    ts: str
    metadata: Mapping[str, Any]
    signature: str | None = None

    def payload(self) -> Mapping[str, Any]:
        return {
            "version": self.version,
            "prev_hash": self.prev_hash,
            "plan_id": self.plan_id,
            "plan_step_id": self.plan_step_id,
            "receipt_path": self.receipt_path,
            "agent_id": self.agent_id,
            "ts": self.ts,
            "metadata": self.metadata,
        }

    def hash(self) -> str:
        return _hash_payload(self.payload())

    def to_json(self) -> Mapping[str, Any]:
        payload = dict(self.payload())
        payload["hash"] = self.hash()
        if self.signature:
            payload["signature"] = self.signature
        return payload


def append_entry(
    *,
    plan_id: str,
    plan_step_id: str | None,
    receipt_path: str | Path,
    agent_id: str,
    timestamp: str,
    metadata: Mapping[str, Any] | None = None,
    metadata_path: Path | None = None,
    signature: str | None = None,
) -> tuple[Path, Mapping[str, Any]]:
    """Append an entry to the ledger and return the stored payload."""

    state = _load_state()
    prev_hash = state.get("tip_hash", "0" * 64)
    receipt_rel = _normalise_receipt_path(receipt_path)
    meta_payload = metadata if metadata is not None else _load_metadata(metadata_path)
    entry = LedgerEntry(
        version=0,
        prev_hash=prev_hash,
        plan_id=plan_id,
        plan_step_id=plan_step_id,
        receipt_path=receipt_rel,
        agent_id=agent_id,
        ts=timestamp,
        metadata=meta_payload,
        signature=signature,
    )
    payload = entry.to_json()
    _ensure_ledger_dir()
    slug = _slug_timestamp(timestamp)
    receipt_file = LEDGER_DIR / f"receipt-{slug}.json"
    receipt_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with INDEX_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, separators=(",", ":")) + "\n")
    new_state = {"tip_hash": payload["hash"], "entry_count": state.get("entry_count", 0) + 1}
    _write_state(new_state)
    return receipt_file, payload


def guard_ledger() -> tuple[bool, list[str], int]:
    """Replay the ledger index and verify hash continuity + receipt existence."""

    if not INDEX_FILE.exists():
        _write_state({"tip_hash": "0" * 64, "entry_count": 0})
        print("ledger guard: no entries")
        return True, [], 0

    prev_hash = "0" * 64
    issues: list[str] = []
    total_entries = 0
    with INDEX_FILE.open(encoding="utf-8") as fh:
        for line_num, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive parsing
                issues.append(f"line {line_num}: invalid json ({exc})")
                continue
            fields = {
                key: payload.get(key)
                for key in (
                    "version",
                    "prev_hash",
                    "plan_id",
                    "plan_step_id",
                    "receipt_path",
                    "agent_id",
                    "ts",
                    "metadata",
                )
            }
            computed_hash = _hash_payload(fields)
            expected_hash = payload.get("hash")
            if expected_hash != computed_hash:
                issues.append(f"line {line_num}: hash mismatch {expected_hash} != {computed_hash}")
            if payload.get("prev_hash") != prev_hash:
                issues.append(f"line {line_num}: prev_hash mismatch {payload.get('prev_hash')} != {prev_hash}")
            receipt_path = ROOT / payload.get("receipt_path", "")
            if not receipt_path.exists():
                issues.append(f"line {line_num}: missing receipt {payload.get('receipt_path')}")
            prev_hash = expected_hash or computed_hash
            total_entries += 1
    if issues:
        print("ledger guard: failures detected")
        for issue in issues:
            print(f"- {issue}")
        return False, issues, total_entries
    _write_state({"tip_hash": prev_hash, "entry_count": total_entries})
    print(f"ledger guard: ok (entries={total_entries})")
    return True, [], total_entries


def cmd_append(args: argparse.Namespace) -> int:
    metadata_path = args.metadata
    if metadata_path and not metadata_path.is_absolute():
        metadata_path = ROOT / metadata_path
    entry_path, payload = append_entry(
        plan_id=args.plan,
        plan_step_id=args.step,
        receipt_path=args.receipt,
        agent_id=args.agent,
        timestamp=args.ts,
        metadata_path=metadata_path,
        signature=args.signature,
    )
    rel_entry = entry_path.relative_to(ROOT)
    print(f"ledger append: {payload['hash']}")
    print(f"entry → {rel_entry}")
    return 0


def cmd_guard(args: argparse.Namespace) -> int:
    ok, _, _ = guard_ledger()
    return 0 if ok else 2


def register_cli(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    sub = parser.add_subparsers(dest="command", required=True)
    append_cmd = sub.add_parser("append", help="Append a new ledger entry")
    append_cmd.add_argument("--plan", required=True)
    append_cmd.add_argument("--step")
    append_cmd.add_argument("--receipt", required=True)
    append_cmd.add_argument("--agent", required=True)
    append_cmd.add_argument("--ts", required=True, help="ISO8601 timestamp")
    append_cmd.add_argument("--metadata", type=Path)
    append_cmd.add_argument("--signature")
    append_cmd.set_defaults(_hash_ledger_handler=cmd_append)

    guard_cmd = sub.add_parser("guard", help="Validate ledger integrity")
    guard_cmd.set_defaults(_hash_ledger_handler=cmd_guard)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    register_cli(parser)
    args = parser.parse_args(argv)
    handler = getattr(args, "_hash_ledger_handler", None)
    if handler is None:
        parser.error("hash_ledger subcommand required")
    return handler(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
