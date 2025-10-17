"""Log structured receipts for evangelism, ethics, or impact events."""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
EVANGELISM_DIR = ROOT / "_report" / "usage" / "evangelism"
ETHICS_DIR = ROOT / "_report" / "usage" / "governance"
IMPACT_LOG_PATH = ROOT / "memory" / "impact" / "log.jsonl"

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now(ts: datetime | None = None) -> str:
    return (ts or _now()).strftime(ISO_FMT)


def _timestamp_slug(ts: datetime | None = None) -> str:
    return (ts or _now()).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def log_evangelism(summary: str, *, channel: str, arc: str, asset: str, status: str,
                   date: str, audience: str | None, link: str | None, notes: str | None) -> Path:
    now = _now()
    payload: dict[str, object] = {
        "event_id": uuid.uuid4().hex,
        "generated_at": _iso_now(now),
        "date": date,
        "channel": channel,
        "arc": arc,
        "asset": asset,
        "status": status,
        "summary": summary,
    }
    if audience:
        payload["audience"] = audience
    if link:
        payload["link"] = link
    if notes:
        payload["notes"] = notes

    EVANGELISM_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"event-{_timestamp_slug(now)}.json"
    path = EVANGELISM_DIR / filename
    _write_json(path, payload)
    return path


def log_ethics(summary: str, *, scenario: str, impact: str,
               actions: Sequence[str] | None, receipts: Sequence[str] | None,
               notes: Sequence[str] | None) -> Path:
    now = _now()
    payload: dict[str, object] = {
        "event_id": uuid.uuid4().hex,
        "generated_at": _iso_now(now),
        "summary": summary,
        "scenario": scenario,
        "impact": impact,
        "actions": list(actions or []),
        "linked_receipts": list(receipts or []),
    }
    if notes:
        payload["notes"] = list(notes)

    ETHICS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"ethics-scenario-{_timestamp_slug(now)}.json"
    path = ETHICS_DIR / filename
    _write_json(path, payload)
    return path


def write_impact_entry(entry: Mapping[str, object], *, dry_run: bool,
                       log_path: Path | None = None) -> None:
    if dry_run:
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return

    path = log_path or IMPACT_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"impact-log: appended entry -> {_relative(path)}")


def log_impact(*, title: str, value: float, currency: str, description: str,
               receipts: Sequence[str], notes: str | None, dry_run: bool,
               log_path: Path | None = None) -> None:
    entry: dict[str, object] = {
        "recorded_at": _iso_now(),
        "title": title,
        "value": value,
        "currency": currency,
        "description": description,
        "receipts": list(receipts),
        "notes": notes,
    }
    write_impact_entry(entry, dry_run=dry_run, log_path=log_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="preset", required=True)

    evangelism = subparsers.add_parser("evangelism", help="Log an evangelism cadence touch")
    evangelism.add_argument("summary", help="Short note describing the touch or outcome")
    evangelism.add_argument("--channel", required=True, help="Channel used (e.g. blog, social, webinar)")
    evangelism.add_argument("--arc", required=True, help="Narrative arc identifier")
    evangelism.add_argument("--asset", required=True, help="Primary asset path referenced")
    evangelism.add_argument(
        "--status",
        default="scheduled",
        choices=["scheduled", "sent", "published", "follow_up"],
        help="Lifecycle status (default: scheduled)",
    )
    evangelism.add_argument(
        "--date",
        default=datetime.utcnow().strftime("%Y-%m-%d"),
        help="Calendar date (YYYY-MM-DD, default: today)",
    )
    evangelism.add_argument("--audience", help="Audience segment or partner")
    evangelism.add_argument("--link", help="External URL or asset path")
    evangelism.add_argument("--notes", help="Optional extended notes")
    evangelism.set_defaults(handler=_handle_evangelism)

    ethics = subparsers.add_parser("ethics", help="Log an ethics scenario receipt")
    ethics.add_argument("summary", help="Short description of the defensive action")
    ethics.add_argument("--scenario", required=True, help="Playbook scenario id")
    ethics.add_argument(
        "--impact",
        choices=["low", "medium", "high"],
        default="medium",
        help="Impact level for disclosure planning (default: medium)",
    )
    ethics.add_argument("--actions", nargs="*", help="Actions taken (repeatable)")
    ethics.add_argument("--receipts", nargs="*", help="Related receipt paths")
    ethics.add_argument("--notes", nargs="*", help="Optional extended notes")
    ethics.set_defaults(handler=_handle_ethics)

    impact = subparsers.add_parser("impact", help="Append an impact ledger entry")
    impact.add_argument("--title", required=True, help="Outcome title")
    impact.add_argument("--value", type=float, required=True, help="Estimated value (numeric)")
    impact.add_argument("--currency", default="USD", help="Currency code (default USD)")
    impact.add_argument("--description", required=True, help="Impact description")
    impact.add_argument("--receipt", action="append", default=[], help="Supporting receipt path (repeatable)")
    impact.add_argument("--notes", help="Optional notes or follow-ups")
    impact.add_argument("--dry-run", action="store_true", help="Print entry without writing")
    impact.set_defaults(handler=_handle_impact)

    return parser


def _handle_evangelism(args: argparse.Namespace) -> int:
    path = log_evangelism(
        args.summary,
        channel=args.channel,
        arc=args.arc,
        asset=args.asset,
        status=args.status,
        date=args.date,
        audience=args.audience,
        link=args.link,
        notes=args.notes,
    )
    print(f"evangelism event logged → {_relative(path)}")
    return 0


def _handle_ethics(args: argparse.Namespace) -> int:
    path = log_ethics(
        args.summary,
        scenario=args.scenario,
        impact=args.impact,
        actions=args.actions,
        receipts=args.receipts,
        notes=args.notes,
    )
    print(f"ethics scenario logged → {_relative(path)}")
    return 0


def _handle_impact(args: argparse.Namespace) -> int:
    log_impact(
        title=args.title,
        value=args.value,
        currency=args.currency,
        description=args.description,
        receipts=args.receipt,
        notes=args.notes,
        dry_run=args.dry_run,
    )
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 2
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
