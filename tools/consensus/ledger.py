#!/usr/bin/env python3
"""Render summaries from the ledger for consensus checkpoints."""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = ROOT / "_report" / "ledger.csv"
DEFAULT_RECEIPT_DIR = ROOT / "_report" / "consensus"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
LEDGER_TS_FMT = "%Y%m%dT%H%M%SZ"


class LedgerError(RuntimeError):
    """Raised when ledger data cannot be processed."""


@dataclass(frozen=True)
class LedgerRow:
    """Row wrapper providing convenience accessors."""

    data: dict[str, str]

    def timestamp(self) -> datetime | None:
        for key in ("decision_ts", "batch_ts", "timestamp"):
            value = self.data.get(key)
            if not value:
                continue
            for fmt in (LEDGER_TS_FMT, ISO_FMT):
                try:
                    return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        return None

    def matches_decision(self, decisions: set[str]) -> bool:
        if not decisions:
            return True
        for key in ("decision_id", "batch_ts", "id"):
            value = self.data.get(key)
            if value and value in decisions:
                return True
        return False

    def matches_agent(self, agents: set[str]) -> bool:
        if not agents:
            return True
        for key in ("agent", "owner", "assignee"):
            value = self.data.get(key)
            if value and value in agents:
                return True
        return False


def parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise LedgerError("--since must be ISO8601 UTC (e.g. 2025-09-18T19:00:00Z)") from exc


def load_rows(path: Path) -> list[LedgerRow]:
    if not path.exists():
        raise LedgerError(f"ledger file not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise LedgerError("ledger has no header row")
        rows = [LedgerRow({key: value or "" for key, value in row.items()}) for row in reader]
    return rows


def filter_rows(
    rows: Iterable[LedgerRow],
    *,
    decisions: set[str],
    agents: set[str],
    since: datetime | None,
) -> list[LedgerRow]:
    selected: list[LedgerRow] = []
    for row in rows:
        if not row.matches_decision(decisions):
            continue
        if not row.matches_agent(agents):
            continue
        ts = row.timestamp()
        if since and ts and ts < since:
            continue
        selected.append(row)
    return selected


def limit_rows(rows: Sequence[LedgerRow], limit: int | None) -> list[LedgerRow]:
    if limit is None or limit <= 0:
        return list(rows)
    return list(rows)[-limit:]


def ordered_fieldnames(rows: Sequence[LedgerRow]) -> list[str]:
    if not rows:
        return []
    keys: list[str] = []
    for row in rows:
        for key in row.data.keys():
            if key not in keys:
                keys.append(key)
    return keys


def iter_json(rows: Sequence[LedgerRow], fieldnames: Sequence[str]) -> Iterator[str]:
    for row in rows:
        payload = {key: row.data.get(key, "") for key in fieldnames}
        yield json.dumps(payload, ensure_ascii=False)


def format_table(rows: Sequence[LedgerRow], fieldnames: Sequence[str]) -> str:
    if not rows:
        return "(no ledger rows matched filters)"
    widths = {
        field: max(len(field), *(len(row.data.get(field, "")) for row in rows))
        for field in fieldnames
    }
    header = " | ".join(field.ljust(widths[field]) for field in fieldnames)
    separator = "-+-".join("-" * widths[field] for field in fieldnames)
    lines = [header, separator]
    for row in rows:
        line = " | ".join(row.data.get(field, "").ljust(widths[field]) for field in fieldnames)
        lines.append(line)
    return "\n".join(lines)


def write_receipt(path: Path, rows: Sequence[LedgerRow], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for line in iter_json(rows, fieldnames):
            handle.write(line + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render consensus ledger summaries")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER), help="Path to ledger CSV (default: %(default)s)")
    parser.add_argument("--format", choices={"table", "jsonl"}, default="table", help="Output format")
    parser.add_argument("--decision", action="append", dest="decisions", help="Filter by decision/batch id (repeatable)")
    parser.add_argument("--agent", action="append", dest="agents", help="Filter by agent id")
    parser.add_argument("--since", help="Filter rows at or after the ISO8601 UTC timestamp")
    parser.add_argument("--limit", type=int, help="Restrict to the last N rows after filtering")
    parser.add_argument("--output", help="Optional path to write JSONL receipt for pipeline usage")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        since = parse_iso8601(args.since)
        ledger_path = Path(args.ledger).expanduser().resolve()
        rows = load_rows(ledger_path)
        filtered = filter_rows(
            rows,
            decisions=set(args.decisions or []),
            agents=set(args.agents or []),
            since=since,
        )
        limited = limit_rows(filtered, args.limit)
        fieldnames = ordered_fieldnames(limited)
        if args.output:
            receipt_path = Path(args.output)
            if not receipt_path.is_absolute():
                receipt_path = DEFAULT_RECEIPT_DIR / receipt_path
            write_receipt(receipt_path, limited, fieldnames)
        if args.format == "jsonl":
            for line in iter_json(limited, fieldnames):
                print(line)
        else:
            print(format_table(limited, fieldnames))
        return 0
    except LedgerError as exc:
        parser.error(str(exc))
    except FileNotFoundError as exc:
        parser.error(f"{exc.strerror}: {exc.filename}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
