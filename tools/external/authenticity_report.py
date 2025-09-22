"""Generate an authenticity dashboard from external summary outputs."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUMMARY = ROOT / "_report" / "usage" / "external-summary.json"
DEFAULT_FEEDBACK = ROOT / "_report" / "usage" / "external-feedback.json"
DEFAULT_MARKDOWN = ROOT / "_report" / "usage" / "external-authenticity.md"
DEFAULT_JSON = ROOT / "_report" / "usage" / "external-authenticity.json"


class AuthenticityReportError(RuntimeError):
    """Raised when the authenticity report cannot be generated."""


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY,
        help="Path to external summary JSON",
    )
    parser.add_argument(
        "--feedback",
        type=Path,
        default=DEFAULT_FEEDBACK,
        help="Optional feedback ledger JSON",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=DEFAULT_MARKDOWN,
        help="Output Markdown dashboard path",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=DEFAULT_JSON,
        help="Output JSON dashboard path",
    )
    return parser.parse_args(argv)


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AuthenticityReportError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AuthenticityReportError(f"Invalid JSON: {path}") from exc


def _load_optional_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _avg(values: List[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def build_dashboard(summary: Dict[str, Any], feedback: Dict[str, Any] | None = None) -> Dict[str, Any]:
    feeds = summary.get("feeds", {})
    authenticity = summary.get("authenticity", {})
    generated_at = datetime.now(timezone.utc).isoformat()

    tier_entries: List[Dict[str, Any]] = []
    all_adjusted: List[float] = []
    attention_feed_rows: List[Dict[str, Any]] = []

    for tier, payload in authenticity.items():
        tier_feeds = payload.get("feeds", [])
        adjusted_values = [feed.get("trust_adjusted") for feed in tier_feeds if feed.get("trust_adjusted") is not None]
        adjusted_values = [float(v) for v in adjusted_values]
        all_adjusted.extend(adjusted_values)
        attention = [feed for feed in tier_feeds if feed.get("status") != "ok"]
        tier_entries.append(
            {
                "tier": tier,
                "weight": payload.get("weight"),
                "feed_count": payload.get("count", len(tier_feeds)),
                "avg_adjusted_trust": _avg(adjusted_values),
                "attention_feeds": [feed.get("feed_id") for feed in attention],
            }
        )
        for feed in attention:
            attention_feed_rows.append(
                {
                    "feed_id": feed.get("feed_id"),
                    "tier": tier,
                    "status": feed.get("status"),
                    "trust_adjusted": feed.get("trust_adjusted"),
                }
            )

    overall_avg = _avg(all_adjusted)
    feedback_entries = feedback.get("entries", []) if feedback else []
    recent_feedback = feedback_entries[:10]

    return {
        "generated_at": generated_at,
        "summary_generated_at": summary.get("generated_at"),
        "total_feeds": len(feeds),
        "overall_avg_trust": overall_avg,
        "tiers": tier_entries,
        "attention_feeds": attention_feed_rows,
        "feedback_entries": recent_feedback,
    }


def _write_json(report: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_markdown(report: Dict[str, Any], path: Path) -> None:
    lines = ["# External Authenticity Dashboard\n"]
    lines.append(f"Generated at: {report['generated_at']}\n")
    if report.get("summary_generated_at"):
        lines.append(f"Summary generated at: {report['summary_generated_at']}\n")
    lines.append(f"Total feeds: {report['total_feeds']}\n")
    lines.append(f"Overall adjusted trust: {report['overall_avg_trust']}\n\n")

    lines.append("## Tiers\n")
    lines.append("| Tier | Weight | Feed count | Avg adjusted trust | Attention feeds |\n")
    lines.append("| --- | --- | --- | --- | --- |\n")
    for tier in report["tiers"]:
        lines.append(
            f"| {tier['tier']} | {tier['weight']} | {tier['feed_count']} | {tier['avg_adjusted_trust']} | "
            f"{', '.join(tier['attention_feeds']) or '—'} |\n"
        )

    if report["attention_feeds"]:
        lines.append("\n## Attention feeds\n")
        lines.append("| Feed | Tier | Status | Adjusted trust |\n")
        lines.append("| --- | --- | --- | --- |\n")
        for feed in report["attention_feeds"]:
            lines.append(
                f"| {feed['feed_id']} | {feed['tier']} | {feed['status']} | {feed['trust_adjusted']} |\n"
            )

    if report["feedback_entries"]:
        lines.append("\n## Recent feedback\n")
        for entry in report["feedback_entries"]:
            note = entry.get("note")
            feed_id = entry.get("feed_id")
            trust = entry.get("trust_adjusted")
            lines.append(f"- **{feed_id}** (trust {trust}): {note}\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def generate_dashboard(
    summary: Dict[str, Any],
    feedback: Dict[str, Any] | None,
    markdown_path: Path,
    json_path: Path,
) -> Dict[str, Any]:
    report = build_dashboard(summary, feedback)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(report, json_path)
    _write_markdown(report, markdown_path)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    summary_path = args.summary if args.summary.is_absolute() else (ROOT / args.summary).resolve()
    feedback_path = args.feedback if args.feedback.is_absolute() else (ROOT / args.feedback).resolve()
    summary_data = _load_json(summary_path)
    feedback_data = _load_optional_json(feedback_path)
    json_out = args.out_json if args.out_json.is_absolute() else (ROOT / args.out_json).resolve()
    md_out = args.out_md if args.out_md.is_absolute() else (ROOT / args.out_md).resolve()
    generate_dashboard(summary_data, feedback_data, md_out, json_out)
    try:
        md_disp = md_out.relative_to(ROOT)
    except ValueError:
        md_disp = md_out
    try:
        json_disp = json_out.relative_to(ROOT)
    except ValueError:
        json_disp = json_out
    print(f"authenticity dashboard: wrote {md_disp} and {json_disp}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
