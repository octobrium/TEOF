"""Generate propagation briefs + receipts for BTC wallet capture."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Sequence

from tools.autonomy import shared


SYSTEMIC_TARGETS = ["S3", "S2", "S6"]
LAYER_TARGETS = ["L4", "L5"]


@dataclass
class Channel:
    name: str
    audience: str
    cta: str
    status: str = "ready"

    def serialize(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "audience": self.audience,
            "cta": self.cta,
            "status": self.status,
        }


def _parse_channel_spec(spec: str) -> Channel:
    parts = [section.strip() for section in spec.split("|")]
    if len(parts) < 3:
        raise SystemExit(f"::error:: invalid channel spec {spec!r}; use name|audience|cta[|status]")
    name, audience, cta = parts[:3]
    status = parts[3] if len(parts) > 3 and parts[3] else "ready"
    if not name or not audience or not cta:
        raise SystemExit(f"::error:: channel spec fields cannot be empty ({spec!r})")
    return Channel(name=name, audience=audience, cta=cta, status=status)


def _load_channels_file(path: Path) -> list[Channel]:
    data = shared.load_json(path)
    if data is None:
        raise SystemExit(f"::error:: unable to read channels file: {path}")
    if not isinstance(data, list):
        raise SystemExit("::error:: channels file must be a list of objects")
    channels: list[Channel] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        audience = entry.get("audience")
        cta = entry.get("cta")
        status = entry.get("status", "ready")
        if not (isinstance(name, str) and isinstance(audience, str) and isinstance(cta, str)):
            continue
        channels.append(Channel(name=name.strip(), audience=audience.strip(), cta=cta.strip(), status=status.strip() or "ready"))
    return channels


def _count_json_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.rglob("*.json"))


def _ledger_summary(path: Path) -> dict[str, Any]:
    total_in = Decimal("0")
    total_out = Decimal("0")
    entries = 0
    last_receipt: str | None = None
    if path.exists():
        for ledger_file in sorted(p for p in path.glob("*.json") if p.is_file()):
            if ledger_file.name == "summary.json":
                continue
            payload = shared.load_json(ledger_file)
            if not isinstance(payload, dict):
                continue
            for entry in payload.get("entries", []) or []:
                if not isinstance(entry, dict):
                    continue
                amount_raw = entry.get("amount_btc", "0")
                try:
                    amount = Decimal(str(amount_raw))
                except (InvalidOperation, TypeError):
                    amount = Decimal("0")
                direction = entry.get("direction")
                if direction == "in":
                    total_in += amount
                elif direction == "out":
                    total_out += amount
                entries += 1
                last_receipt = ledger_file.as_posix()
    balance = total_in - total_out
    return {
        "entries": entries,
        "total_in_btc": f"{total_in:.8f}",
        "total_out_btc": f"{total_out:.8f}",
        "balance_btc": f"{balance:.8f}",
        "last_receipt": last_receipt,
    }


def _ensure_channels(args: argparse.Namespace) -> list[Channel]:
    channels: list[Channel] = []
    if args.channel:
        channels.extend(_parse_channel_spec(spec) for spec in args.channel)
    if args.channels_file:
        channels.extend(_load_channels_file(args.channels_file))
    if not channels:
        raise SystemExit("::error:: define at least one channel via --channel or --channels-file")
    return channels


def _sanitise_timestamp(ts: str) -> str:
    return ts.replace("-", "").replace(":", "")


def _write_cta_file(base: Path, run_id: str, channel: Channel, plan_id: str, generated_at: str) -> Path:
    channel_dir = base / run_id
    channel_dir.mkdir(parents=True, exist_ok=True)
    file_path = channel_dir / f"{channel.name}.md"
    content = (
        f"# Propagation CTA — {channel.name}\n\n"
        f"- Audience: {channel.audience}\n"
        f"- Plan: {plan_id}\n"
        f"- Generated: {generated_at}\n\n"
        f"{channel.cta.strip()}\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _build_payload(
    *,
    plan_id: str,
    channels: list[Channel],
    notes: str | None,
    next_check: str | None,
    output_dir: Path,
    artifacts_dir: Path,
) -> tuple[Path, dict[str, Any]]:
    generated_at = shared.utc_timestamp()
    run_id = f"propagation-{_sanitise_timestamp(generated_at)}"
    receipt_path = output_dir / f"{run_id}.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[dict[str, Any]] = []
    channel_payload: list[dict[str, Any]] = []
    for channel in channels:
        artifact_path = _write_cta_file(artifacts_dir, run_id, channel, plan_id, generated_at)
        channel_entry = channel.serialize()
        channel_entry["linked_artifacts"] = [artifact_path.as_posix()]
        channel_payload.append(channel_entry)
        artifacts.append({"channel": channel.name, "path": artifact_path.as_posix()})

    stats = {
        "ledger": _ledger_summary(Path("_report/impact/btc-ledger")),
        "tier1_receipts": _count_json_files(Path("_report/usage/onboarding")),
        "contributor_receipts": _count_json_files(Path("_report/usage/contributors")),
        "propagation_receipts": _count_json_files(output_dir),
    }

    payload: dict[str, Any] = {
        "version": 1,
        "plan_id": plan_id,
        "generated_at": generated_at,
        "run_id": run_id,
        "notes": notes or "",
        "next_check": next_check or generated_at,
        "systemic_targets": SYSTEMIC_TARGETS,
        "layer_targets": LAYER_TARGETS,
        "channels": channel_payload,
        "artifacts": artifacts,
        "stats": stats,
    }
    git_hash = shared.git_commit(Path(".").resolve())
    if git_hash:
        payload["git_commit"] = git_hash
    return receipt_path, payload


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="Plan ID this propagation run advances")
    parser.add_argument(
        "--channel",
        action="append",
        help="Channel definition `name|audience|cta[|status]` (repeatable)",
    )
    parser.add_argument(
        "--channels-file",
        type=Path,
        help="JSON file containing channel objects",
    )
    parser.add_argument("--notes", help="Optional run note")
    parser.add_argument("--next-check", help="ISO timestamp for follow-up (defaults to generated time)")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("_report/impact/propagation"),
        help="Directory for propagation receipts",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts/propagation"),
        help="Directory for generated CTA artifacts",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print payload instead of writing receipt")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    channels = _ensure_channels(args)
    receipt_path, payload = _build_payload(
        plan_id=args.plan,
        channels=channels,
        notes=args.notes,
        next_check=args.next_check,
        output_dir=args.output_dir,
        artifacts_dir=args.artifacts_dir,
    )
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    shared.write_receipt_payload(receipt_path, payload)
    print(f"propagate: recorded receipt {receipt_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
