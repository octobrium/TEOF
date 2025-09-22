"""Append authenticity snapshots to the daily Chronicle."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MARKDOWN = ROOT / "docs" / "usage" / "chronicle.md"
DEFAULT_LEDGER_DIR = ROOT / "_report" / "usage" / "chronicle"
DEFAULT_ENTRY_LIMIT = 14

_HEADER = "# Authenticity Chronicle"


def _ensure_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return datetime.now(timezone.utc)


def _round(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return round(float(value), 3)
    return None


def _build_entry(summary: Mapping[str, Any]) -> dict[str, Any]:
    generated = _ensure_datetime(summary.get("generated_at"))
    feeds_payload = summary.get("feeds")
    feeds: list[dict[str, Any]] = []
    adjustments: list[float] = []

    if isinstance(feeds_payload, Mapping):
        for feed_id, payload in feeds_payload.items():
            if not isinstance(payload, Mapping):
                continue
            trust = payload.get("trust") if isinstance(payload.get("trust"), Mapping) else {}
            authenticity = payload.get("authenticity") if isinstance(payload.get("authenticity"), Mapping) else {}
            steward = payload.get("steward") if isinstance(payload.get("steward"), Mapping) else {}

            adjusted = trust.get("adjusted") if isinstance(trust, Mapping) else None
            if isinstance(adjusted, (int, float)):
                adjustments.append(float(adjusted))

            feeds.append(
                {
                    "feed_id": feed_id,
                    "tier": authenticity.get("tier"),
                    "status": trust.get("status"),
                    "adjusted_trust": _round(adjusted),
                    "baseline_trust": _round((trust or {}).get("baseline")),
                    "steward_id": steward.get("id") if isinstance(steward.get("id"), str) else None,
                }
            )

    authenticity_index = summary.get("authenticity")
    tiers: list[dict[str, Any]] = []
    attention: list[dict[str, Any]] = []
    if isinstance(authenticity_index, Mapping):
        for tier_name, payload in authenticity_index.items():
            if not isinstance(payload, Mapping):
                continue
            feeds_list = payload.get("feeds", [])
            tier_attention: list[str] = []
            if isinstance(feeds_list, Sequence):
                for feed in feeds_list:
                    if not isinstance(feed, Mapping):
                        continue
                    status = feed.get("status")
                    if status and status != "ok":
                        feed_id = str(feed.get("feed_id", "")).strip()
                        tier_attention.append(feed_id)
                        attention.append(
                            {
                                "feed_id": feed_id or None,
                                "tier": tier_name,
                                "status": status,
                                "trust_adjusted": _round(feed.get("trust_adjusted")),
                            }
                        )
            tiers.append(
                {
                    "tier": tier_name,
                    "weight": payload.get("weight"),
                    "feed_count": payload.get("count")
                    if isinstance(payload.get("count"), int)
                    else len(feeds_list) if isinstance(feeds_list, Sequence) else 0,
                    "avg_adjusted_trust": _round(payload.get("avg_adjusted_trust")),
                    "attention_feeds": tier_attention,
                }
            )

    overall = round(sum(adjustments) / len(adjustments), 3) if adjustments else None
    return {
        "generated_at": generated.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall_adjusted_trust": overall,
        "feed_count": len(feeds),
        "tiers": tiers,
        "feeds": feeds,
        "attention_feeds": attention,
        "source": "external-summary",
    }


def _render_markdown(entry: Mapping[str, Any]) -> str:
    timestamp = entry.get("generated_at", "unknown")
    overall = entry.get("overall_adjusted_trust")
    feed_count = entry.get("feed_count", 0)
    tiers = entry.get("tiers", [])
    attention = entry.get("attention_feeds", [])
    feeds = entry.get("feeds", [])

    lines: list[str] = []
    lines.append(f"## {timestamp} — Authenticity Snapshot")
    lines.append("")
    if overall is not None:
        lines.append(f"- Overall adjusted trust: {overall:.3f}")
    else:
        lines.append("- Overall adjusted trust: unknown")
    lines.append(f"- Tracked feeds: {feed_count}")
    if attention:
        lines.append(
            "- Attention feeds: "
            + ", ".join(
                f"{item.get('feed_id')} ({item.get('status')})" for item in attention if item.get("feed_id")
            )
        )
    else:
        lines.append("- Attention feeds: none")
    lines.append("")
    if tiers:
        lines.append("| Tier | Avg trust | Feed count | Attention |")
        lines.append("| --- | --- | --- | --- |")
        for tier in tiers:
            attention_list = tier.get("attention_feeds") or []
            attention_display = ", ".join(attention_list) if attention_list else "—"
            avg = tier.get("avg_adjusted_trust")
            avg_display = f"{avg:.3f}" if isinstance(avg, (int, float)) else "—"
            lines.append(
                f"| {tier.get('tier')} | {avg_display} | {tier.get('feed_count', 0)} | {attention_display} |"
            )
        lines.append("")
    if feeds:
        lines.append("| Feed | Tier | Adjusted | Status | Steward |")
        lines.append("| --- | --- | --- | --- | --- |")
        for feed in feeds:
            adjusted = feed.get("adjusted_trust")
            adjusted_str = f"{adjusted:.3f}" if isinstance(adjusted, (int, float)) else "—"
            lines.append(
                f"| {feed.get('feed_id')} | {feed.get('tier')} | {adjusted_str} | {feed.get('status', '—')} | {feed.get('steward_id') or '—'} |"
            )
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _parse_existing_sections(text: str) -> list[str]:
    content = text.strip()
    if not content:
        return []
    if content.startswith(_HEADER):
        content = content[len(_HEADER) :].lstrip()
    if not content:
        return []
    parts = content.split("\n## ")
    sections: list[str] = []
    for idx, part in enumerate(parts):
        if not part:
            continue
        if idx == 0 and part.startswith("## "):
            sections.append(part)
        elif idx == 0:
            sections.append("## " + part)
        else:
            sections.append("## " + part)
    return sections


def _write_markdown(entry_md: str, path: Path, *, max_entries: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_sections = []
    if path.exists():
        existing_sections = _parse_existing_sections(path.read_text(encoding="utf-8"))
    sections = [entry_md.strip()] + existing_sections
    if max_entries >= 1:
        sections = sections[:max_entries]
    body = "\n\n".join(section.strip() for section in sections if section.strip())
    content = f"{_HEADER}\n\n{body}\n"
    path.write_text(content, encoding="utf-8")


def _write_ledger(entry: Mapping[str, Any], ledger_dir: Path) -> Path:
    ledger_dir.mkdir(parents=True, exist_ok=True)
    generated = _ensure_datetime(entry.get("generated_at"))
    filename = generated.strftime("%Y%m%dT%H%M%SZ.json")
    path = ledger_dir / filename
    path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def record_entry(
    summary: Mapping[str, Any],
    *,
    markdown_path: Path | None = None,
    ledger_dir: Path | None = None,
    max_entries: int | None = None,
) -> dict[str, Any]:
    """Record a Chronicle entry for the given authenticity summary."""

    markdown_path = markdown_path or DEFAULT_MARKDOWN
    ledger_dir = ledger_dir or DEFAULT_LEDGER_DIR
    entry = _build_entry(summary)
    _write_ledger(entry, ledger_dir)
    entry_md = _render_markdown(entry)
    _write_markdown(entry_md, markdown_path, max_entries=max_entries or DEFAULT_ENTRY_LIMIT)
    return entry


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path, help="Path to external summary JSON")
    parser.add_argument("--markdown", type=Path, help="Output Markdown path (default docs/usage/chronicle.md)")
    parser.add_argument(
        "--ledger-dir",
        type=Path,
        help="Directory for JSON ledger entries (default _report/usage/chronicle)",
    )
    parser.add_argument("--max-entries", type=int, default=DEFAULT_ENTRY_LIMIT, help="Retain at most this many entries in Markdown")
    args = parser.parse_args(argv)

    summary_path = args.summary if args.summary.is_absolute() else (ROOT / args.summary)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    markdown_path = args.markdown if args.markdown is not None else DEFAULT_MARKDOWN
    if not markdown_path.is_absolute():
        markdown_path = ROOT / markdown_path
    ledger_dir = args.ledger_dir if args.ledger_dir is not None else DEFAULT_LEDGER_DIR
    if not ledger_dir.is_absolute():
        ledger_dir = ROOT / ledger_dir
    record_entry(data, markdown_path=markdown_path, ledger_dir=ledger_dir, max_entries=args.max_entries)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
