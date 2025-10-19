"""Append a BTC ledger entry with receipts and checksum."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Sequence

from tools.autonomy.shared import write_receipt_payload


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise SystemExit(f"::error:: invalid JSON in {path}: {exc}") from exc
    except FileNotFoundError:
        raise SystemExit(f"::error:: ledger file not found: {path}")


def _normalise_amount(value: str) -> str:
    try:
        amount = float(value)
    except ValueError as exc:
        raise SystemExit(f"::error:: amount must be numeric, got {value!r}") from exc
    return f"{amount:.8f}"


def _parse_timestamp(value: str | None) -> str:
    if value:
        try:
            dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value
        except ValueError as exc:
            raise SystemExit(f"::error:: invalid ISO timestamp: {value!r}") from exc
    return dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _update_ledger(
    *,
    ledger_path: Path,
    txid: str,
    direction: str,
    amount_btc: str,
    observed_at: str,
    block_height: int,
    evidence: Sequence[str],
    linked_work: Sequence[str],
    notes: str,
) -> dict:
    if direction not in {"in", "out"}:
        raise SystemExit("::error:: direction must be 'in' or 'out'")

    ledger = _load_json(ledger_path)
    entries = ledger.setdefault("entries", [])
    entry = {
        "txid": txid,
        "direction": direction,
        "amount_btc": amount_btc,
        "observed_at": observed_at,
        "block_height": int(block_height),
        "evidence": list(evidence),
        "linked_work": list(linked_work),
        "notes": notes,
    }
    entries.append(entry)
    ledger["generated_at"] = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return ledger


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True, help="Path to ledger JSON file")
    parser.add_argument("--txid", required=True, help="Bitcoin transaction id")
    parser.add_argument("--direction", choices=("in", "out"), required=True, help="Fund direction")
    parser.add_argument("--amount", required=True, help="Amount in BTC (will be normalised to 8dp)")
    parser.add_argument("--observed-at", help="ISO timestamp (defaults to now)")
    parser.add_argument("--block-height", type=int, required=True, help="Block height containing the transaction")
    parser.add_argument("--evidence", action="append", default=[], help="Receipt/evidence paths (repeatable)")
    parser.add_argument("--linked-work", action="append", default=[], help="Related plans or receipts (repeatable)")
    parser.add_argument("--notes", default="", help="Short human note (<=160 chars recommended)")
    parser.add_argument("--dry-run", action="store_true", help="Print updated ledger JSON without writing")
    args = parser.parse_args(list(argv) if argv is not None else None)

    ledger_path = args.ledger
    amount = _normalise_amount(args.amount)
    observed_at = _parse_timestamp(args.observed_at)
    ledger = _update_ledger(
        ledger_path=ledger_path,
        txid=args.txid,
        direction=args.direction,
        amount_btc=amount,
        observed_at=observed_at,
        block_height=args.block_height,
        evidence=args.evidence,
        linked_work=args.linked_work,
        notes=args.notes.strip(),
    )

    if args.dry_run:
        print(json.dumps(ledger, ensure_ascii=False, indent=2))
        return 0

    write_receipt_payload(ledger_path, ledger)
    print(f"btc_record: appended entry for {args.txid} ({args.direction} {amount} BTC)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
