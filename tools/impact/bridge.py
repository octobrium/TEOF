"""Bridge impact ledger entries to backlog plans and receipts."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.autonomy.shared import load_backlog_items, write_receipt_payload


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IMPACT_LOG = ROOT / "memory" / "impact" / "log.jsonl"
DEFAULT_PLANS_DIR = ROOT / "_plans"
DEFAULT_BACKLOG = ROOT / "_plans" / "next-development.todo.json"
DEFAULT_REPORT_DIR = ROOT / "_report" / "impact" / "bridge"

SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class ImpactEntry:
    slug: str
    title: str
    recorded_at: str | None
    value: float | None
    currency: str | None
    description: str | None
    receipts: list[str]
    notes: str | None
    raw: Mapping[str, Any] = field(repr=False)


@dataclass
class PlanRecord:
    plan_id: str
    impact_ref: str | None
    summary: str | None
    status: str | None
    priority: int | None
    path: str
    queue_refs: list[str]
    receipts: list[str]
    backlog_items: list[dict[str, Any]] = field(default_factory=list)


def _slugify(text: str | None, fallback: str) -> str:
    if not text:
        return fallback
    slug = SLUG_PATTERN.sub("-", text.lower()).strip("-")
    return slug or fallback


def _load_json_line(line: str) -> Mapping[str, Any] | None:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, Mapping) else None


def load_impact_entries(path: Path) -> list[ImpactEntry]:
    if not path.exists():
        return []
    entries: list[ImpactEntry] = []
    seen: set[str] = set()
    for idx, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        payload = _load_json_line(raw_line.strip())
        if payload is None:
            continue
        title = str(payload.get("title") or payload.get("name") or f"impact-{idx}")
        slug_candidate = payload.get("slug")
        slug = _slugify(str(slug_candidate) if slug_candidate else title, f"impact-{idx}")
        base_slug = slug
        suffix = 2
        while slug in seen:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        seen.add(slug)
        recorded = payload.get("recorded_at")
        receipts = payload.get("receipts")
        if not isinstance(receipts, Sequence):
            receipts = []
        normalized_receipts = [str(item) for item in receipts if isinstance(item, str)]
        value = payload.get("value")
        if isinstance(value, (int, float)):
            value_num: float | None = float(value)
        else:
            value_num = None
        entry = ImpactEntry(
            slug=slug,
            title=title,
            recorded_at=str(recorded) if isinstance(recorded, str) else None,
            value=value_num,
            currency=str(payload.get("currency")) if payload.get("currency") else None,
            description=str(payload.get("description")) if payload.get("description") else None,
            receipts=normalized_receipts,
            notes=str(payload.get("notes")) if payload.get("notes") else None,
            raw=payload,
        )
        entries.append(entry)
    return entries


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def load_plan_records(plans_dir: Path) -> list[PlanRecord]:
    records: list[PlanRecord] = []
    if not plans_dir.exists():
        return records
    plan_paths = sorted(plans_dir.rglob("*.plan.json"))
    for plan_path in plan_paths:
        try:
            data = json.loads(plan_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        plan_id = str(data.get("plan_id") or plan_path.stem)
        impact_ref = data.get("impact_ref")
        if isinstance(impact_ref, str):
            impact_ref = _slugify(impact_ref, impact_ref)
        else:
            impact_ref = None
        queue_refs = []
        for link in data.get("links") or []:
            if isinstance(link, Mapping) and link.get("type") == "queue":
                ref = link.get("ref")
                if isinstance(ref, str):
                    queue_refs.append(ref)
        receipts = [entry for entry in data.get("receipts", []) if isinstance(entry, str)]
        record = PlanRecord(
            plan_id=plan_id,
            impact_ref=impact_ref,
            summary=str(data.get("summary")) if data.get("summary") else None,
            status=str(data.get("status")) if data.get("status") else None,
            priority=data.get("priority") if isinstance(data.get("priority"), int) else None,
            path=_relative(plan_path),
            queue_refs=queue_refs,
            receipts=receipts,
        )
        records.append(record)
    return records


def build_backlog_index(backlog_path: Path) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    items = load_backlog_items(backlog_path)
    index: dict[str, list[dict[str, Any]]] = {}
    unresolved: list[dict[str, Any]] = []
    for item in items:
        plan_id = item.get("plan_suggestion")
        if isinstance(plan_id, str) and plan_id:
            index.setdefault(plan_id, []).append(
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "status": item.get("status"),
                    "priority": item.get("priority"),
                    "layer": item.get("layer"),
                }
            )
        else:
            unresolved.append(item)
    return index, unresolved


def assemble_report(
    *,
    impact_log: Path,
    plans_dir: Path,
    backlog_path: Path,
) -> dict[str, Any]:
    entries = load_impact_entries(impact_log)
    plans = load_plan_records(plans_dir)
    backlog_index, backlog_without_plan = build_backlog_index(backlog_path)
    plan_index = {plan.plan_id: plan for plan in plans}
    for plan_id, refs in backlog_index.items():
        record = plan_index.get(plan_id)
        if record:
            record.backlog_items.extend(refs)

    ledger_map = {entry.slug: {"entry": entry, "plans": [], "backlog": []} for entry in entries}
    missing_ref: list[PlanRecord] = []
    orphan_ref: list[PlanRecord] = []
    for plan in plans:
        if not plan.impact_ref:
            missing_ref.append(plan)
            continue
        bucket = ledger_map.get(plan.impact_ref)
        if bucket is None:
            orphan_ref.append(plan)
            continue
        bucket["plans"].append(plan)
        bucket["backlog"].extend(plan.backlog_items)

    unused_entries = [slug for slug, bucket in ledger_map.items() if not bucket["plans"]]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    stats = {
        "ledger_entries": len(entries),
        "plans_total": len(plans),
        "plans_with_impact_ref": len(plans) - len(missing_ref),
        "plans_linked": sum(1 for bucket in ledger_map.values() if bucket["plans"]),
        "backlog_with_plan": sum(len(plan.backlog_items) for plan in plans),
        "missing_impact_ref": len(missing_ref),
        "orphan_impact_refs": len(orphan_ref),
        "unused_impact_entries": len(unused_entries),
    }

    serialized_entries = []
    for slug, bucket in sorted(ledger_map.items()):
        entry = bucket["entry"]
        serialized_entries.append(
            {
                "slug": slug,
                "title": entry.title,
                "recorded_at": entry.recorded_at,
                "value": entry.value,
                "currency": entry.currency,
                "description": entry.description,
                "notes": entry.notes,
                "receipts": entry.receipts,
                "linked_plans": [
                    {
                        "plan_id": plan.plan_id,
                        "path": plan.path,
                        "status": plan.status,
                        "priority": plan.priority,
                        "queue_refs": plan.queue_refs,
                        "backlog": plan.backlog_items,
                        "receipts": plan.receipts,
                    }
                    for plan in bucket["plans"]
                ],
                "linked_backlog": bucket["backlog"],
            }
        )

    report = {
        "generated_at": now,
        "inputs": {
            "impact_log": _relative(impact_log),
            "plans_dir": _relative(plans_dir),
            "backlog": _relative(backlog_path),
        },
        "stats": stats,
        "entries": serialized_entries,
        "missing_impact_ref": [
            {"plan_id": plan.plan_id, "path": plan.path, "status": plan.status}
            for plan in missing_ref
        ],
        "orphan_impact_ref": [
            {"plan_id": plan.plan_id, "impact_ref": plan.impact_ref, "path": plan.path}
            for plan in orphan_ref
        ],
        "backlog_without_plan_suggestion": backlog_without_plan,
        "unused_impact_entries": unused_entries,
    }
    return report


def build_markdown(report: Mapping[str, Any]) -> str:
    stats = report.get("stats", {})
    lines = [
        "# Impact Bridge Dashboard",
        "",
        "- Command: teof impact_bridge",
        f"- Generated at: {report.get('generated_at')}",
        f"- Impact ledger entries: {stats.get('ledger_entries', 0)}",
        f"- Plans with impact_ref: {stats.get('plans_with_impact_ref', 0)} / {stats.get('plans_total', 0)}",
        f"- Plans linked to ledger: {stats.get('plans_linked', 0)}",
        f"- Missing impact_ref: {stats.get('missing_impact_ref', 0)}",
        f"- Orphan impact_ref: {stats.get('orphan_impact_refs', 0)}",
        f"- Unused impact entries: {stats.get('unused_impact_entries', 0)}",
        "",
        "## Linked Entries",
        "",
        "| Impact Slug | Plans | Backlog IDs | Receipts |",
        "| --- | --- | --- | --- |",
    ]
    entries = report.get("entries") or []
    if not entries:
        lines.append("| _none_ | – | – | – |")
    else:
        for entry in entries:
            plans = entry.get("linked_plans") or []
            backlog = entry.get("linked_backlog") or []
            plan_list = ", ".join(plan.get("plan_id", "-") for plan in plans) or "—"
            backlog_list = ", ".join(str(item.get("id")) for item in backlog if item.get("id")) or "—"
            receipt_count = len(entry.get("receipts") or [])
            lines.append(
                f"| `{entry.get('slug')}` | {plan_list} | {backlog_list} | {receipt_count} |"
            )
    if report.get("missing_impact_ref"):
        lines.extend(
            [
                "",
                "## Plans Missing impact_ref",
                "",
                "| Plan | Path | Status |",
                "| --- | --- | --- |",
            ]
        )
        for plan in report["missing_impact_ref"]:
            lines.append(
                f"| {plan.get('plan_id')} | `{plan.get('path')}` | {plan.get('status') or '-'} |"
            )
    if report.get("orphan_impact_ref"):
        lines.extend(
            [
                "",
                "## Orphan impact_ref",
                "",
                "| Plan | impact_ref | Path |",
                "| --- | --- | --- |",
            ]
        )
        for plan in report["orphan_impact_ref"]:
            lines.append(
                f"| {plan.get('plan_id')} | `{plan.get('impact_ref')}` | `{plan.get('path')}` |"
            )
    return "\n".join(lines) + "\n"


def _default_summary_path(report_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir / f"impact-bridge-{stamp}.json"


def _default_markdown_path(report_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir / f"impact-bridge-dashboard-{stamp}.md"


def configure_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--impact-log", type=Path, default=DEFAULT_IMPACT_LOG, help="Path to impact log JSONL")
    parser.add_argument("--plans-dir", type=Path, default=DEFAULT_PLANS_DIR, help="Directory containing *.plan.json")
    parser.add_argument("--backlog", type=Path, default=DEFAULT_BACKLOG, help="Backlog todo JSON path")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR, help="Output directory for receipts")
    parser.add_argument("--summary", type=Path, help="Optional explicit JSON summary path")
    parser.add_argument("--markdown", type=Path, help="Optional explicit markdown path")
    parser.add_argument("--orphans-out", type=Path, help="Optional path to write orphan summary JSON")
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Console output format after receipts are generated (default: summary)",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Exit with non-zero status when plans miss or orphan impact references",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing receipts (useful for CI guards that only need exit status)",
    )
    return parser


def _resolve_relative(path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else (ROOT / path)


def run_with_namespace(args: argparse.Namespace) -> int:
    impact_log = _resolve_relative(args.impact_log)
    plans_dir = _resolve_relative(args.plans_dir)
    backlog_path = _resolve_relative(args.backlog)
    if impact_log is None or plans_dir is None or backlog_path is None:
        raise SystemExit("impact_bridge: impact log, plans dir, and backlog path are required")

    report = assemble_report(
        impact_log=impact_log,
        plans_dir=plans_dir,
        backlog_path=backlog_path,
    )
    receipt_payload = dict(report)
    receipt_payload.setdefault("meta", {})
    if isinstance(receipt_payload["meta"], dict):
        receipt_payload["meta"]["command"] = "impact_bridge"
        receipt_payload["meta"]["cli"] = "teof impact_bridge"
    report_dir = _resolve_relative(args.report_dir) or DEFAULT_REPORT_DIR

    summary_path = markdown_path = None
    if not args.no_write:
        report_dir.mkdir(parents=True, exist_ok=True)

        summary_path = _resolve_relative(args.summary)
        if summary_path is None:
            summary_path = _default_summary_path(report_dir)
        else:
            summary_path.parent.mkdir(parents=True, exist_ok=True)
        write_receipt_payload(summary_path, receipt_payload)

        markdown_path = _resolve_relative(args.markdown)
        if markdown_path is None:
            markdown_path = _default_markdown_path(report_dir)
        else:
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(build_markdown(report), encoding="utf-8")
    else:
        if args.format == "summary":
            print("impact bridge check completed (--no-write)")

    rel_summary = _relative(summary_path) if summary_path else None
    rel_markdown = _relative(markdown_path) if markdown_path else None

    if args.orphans_out:
        out_path = _resolve_relative(args.orphans_out)
        if out_path is None:
            raise SystemExit("--orphans-out path invalid")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": report.get("generated_at"),
            "missing_impact_ref": report.get("missing_impact_ref", []),
            "orphan_impact_ref": report.get("orphan_impact_ref", []),
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.format == "json":
        console_payload = dict(report)
        console_payload["receipts"] = {
            "summary": rel_summary,
            "markdown": rel_markdown,
        }
        print(json.dumps(console_payload, ensure_ascii=False, indent=2))
    else:
        stats = report.get("stats", {})
        print("Impact Bridge Stats:")
        print(f"- ledger entries     : {stats.get('ledger_entries', 0)}")
        print(f"- plans total        : {stats.get('plans_total', 0)}")
        print(f"- plans linked       : {stats.get('plans_linked', 0)}")
        print(f"- backlog with plans : {stats.get('backlog_with_plan', 0)}")
        print(f"- missing impact_ref : {stats.get('missing_impact_ref', 0)}")
        print(f"- orphan impact_ref  : {stats.get('orphan_impact_refs', 0)}")
        missing = report.get("missing_impact_ref") or []
        orphan = report.get("orphan_impact_ref") or []
        unused = report.get("unused_impact_entries") or []
        if missing:
            sample = ", ".join(plan.get("plan_id", "-") for plan in missing[:5])
            if len(missing) > 5:
                sample += ", …"
            print(f"  → missing impact_ref plans: {sample}")
        if orphan:
            sample = ", ".join(plan.get("plan_id", "-") for plan in orphan[:5])
            if len(orphan) > 5:
                sample += ", …"
            print(f"  → orphan impact_ref plans: {sample}")
        if unused:
            preview = ", ".join(unused[:5])
            if len(unused) > 5:
                preview += ", …"
            print(f"  → ledger entries without plans: {preview}")
        if rel_summary:
            print(f"impact bridge summary  → {rel_summary}")
        if rel_markdown:
            print(f"impact bridge dashboard → {rel_markdown}")

    stats = report.get("stats", {})
    if args.fail_on_missing:
        if stats.get("missing_impact_ref") or stats.get("orphan_impact_refs"):
            return 1
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    configure_parser(parser)
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Sequence[str] | None = None) -> int:
    return run_with_namespace(parse_args(argv))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
