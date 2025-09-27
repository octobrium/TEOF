"""Summarise repository receipt health."""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

ROOT = Path(__file__).resolve().parents[2]
RECEIPT_ROOT = ROOT / "docs" / "receipts"
ATTACHMENTS = {
    "attest": RECEIPT_ROOT / "attest",
    "manual": RECEIPT_ROOT / "manual-verification",
}

Verdict = Literal["PASS", "FAIL", "UNKNOWN"]


@dataclass(frozen=True)
class ReceiptSummary:
    kind: str
    path: Path
    timestamp: dt.datetime | None
    verdict: Verdict

    @property
    def ok(self) -> bool:
        return self.verdict == "PASS"


def _parse_iso8601(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _summaries_for_dir(kind: str, directory: Path) -> list[ReceiptSummary]:
    if not directory.exists():
        return []
    summaries: list[ReceiptSummary] = []
    for receipt_path in sorted(directory.glob("*/receipt.json")):
        data = _load_json(receipt_path)
        ts = data.get("timestamp") or data.get("generated_at")
        verdict: Verdict
        if "verdict" in data:
            verdict = str(data.get("verdict") or "UNKNOWN").upper()  # type: ignore[assignment]
            if verdict not in ("PASS", "FAIL"):
                verdict = "UNKNOWN"
        else:
            verdict = "PASS"
        summaries.append(
            ReceiptSummary(
                kind=kind,
                path=receipt_path.relative_to(ROOT),
                timestamp=_parse_iso8601(ts),
                verdict=verdict,
            )
        )
    return summaries


def collect_receipts(kinds: Iterable[str] | None = None) -> list[ReceiptSummary]:
    selected = kinds or ATTACHMENTS.keys()
    receipts: list[ReceiptSummary] = []
    for kind in selected:
        base = ATTACHMENTS.get(kind)
        if base is None:
            continue
        receipts.extend(_summaries_for_dir(kind, base))
    return receipts


def build_overview(receipts: Iterable[ReceiptSummary]) -> dict[str, dict[str, object]]:
    overview: dict[str, dict[str, object]] = {}
    for summary in receipts:
        bucket = overview.setdefault(
            summary.kind,
            {
                "total": 0,
                "passes": 0,
                "fails": 0,
                "latest": None,
            },
        )
        bucket["total"] = int(bucket["total"]) + 1
        if summary.ok:
            bucket["passes"] = int(bucket["passes"]) + 1
        else:
            bucket["fails"] = int(bucket["fails"]) + 1
            failures = bucket.setdefault("failures", [])
            failures.append(summary)
        latest: tuple[dt.datetime | None, ReceiptSummary] | None = bucket["latest"]  # type: ignore[assignment]
        current = (summary.timestamp, summary)
        if latest is None or (current[0] or dt.datetime.min) > (latest[0] or dt.datetime.min):
            bucket["latest"] = current
    return overview


def format_table(overview: dict[str, dict[str, object]]) -> str:
    if not overview:
        return "No receipts found."
    headers = ["Kind", "Total", "Pass", "Fail", "Latest (UTC)", "Verdict", "Path"]
    rows: list[list[str]] = []
    for kind in sorted(overview):
        bucket = overview[kind]
        latest_tuple = bucket.get("latest")
        latest_summary: ReceiptSummary | None = None
        latest_ts: dt.datetime | None = None
        if latest_tuple is not None:
            latest_ts, latest_summary = latest_tuple  # type: ignore[misc]
        rows.append(
            [
                kind,
                str(bucket.get("total", 0)),
                str(bucket.get("passes", 0)),
                str(bucket.get("fails", 0)),
                latest_ts.isoformat().replace("+00:00", "Z") if latest_ts else "—",
                latest_summary.verdict if latest_summary else "—",
                str(latest_summary.path) if latest_summary else "—",
            ]
        )
    widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]

    def fmt(row: list[str]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    lines = [fmt(headers), " | ".join("-" * widths[i] for i in range(len(headers)))]
    lines.extend(fmt(row) for row in rows)
    return "\n".join(lines)


def overall_status(overview: dict[str, dict[str, object]]) -> str:
    if not overview:
        return "UNKNOWN"
    if any(bucket.get("fails", 0) for bucket in overview.values()):
        return "FAIL"
    return "PASS"


def status_summary(kinds: Iterable[str] | None = None) -> tuple[str, dict[str, dict[str, object]]]:
    receipts = collect_receipts(kinds)
    overview = build_overview(receipts)
    status = overall_status(overview)
    return status, overview


def cli_status(kinds: Iterable[str] | None = None, *, output_format: str = "table") -> int:
    status, overview = status_summary(kinds)
    if output_format == "json":
        payload = {
            "status": status,
            "kinds": {
                kind: {
                    "total": bucket.get("total", 0),
                    "passes": bucket.get("passes", 0),
                    "fails": bucket.get("fails", 0),
                    "failures": [
                        {
                            "timestamp": (
                                item.timestamp.isoformat().replace("+00:00", "Z")
                                if item.timestamp
                                else None
                            ),
                            "path": str(item.path),
                            "verdict": item.verdict,
                        }
                        for item in bucket.get("failures", [])
                    ],
                    "latest": (
                        {
                            "timestamp": (
                                latest_tuple[0].isoformat().replace("+00:00", "Z")
                                if latest_tuple and latest_tuple[0]
                                else None
                            ),
                            "verdict": latest_tuple[1].verdict if latest_tuple else None,
                            "path": str(latest_tuple[1].path) if latest_tuple else None,
                        }
                        if (latest_tuple := bucket.get("latest"))
                        else None
                    ),
                }
                for kind, bucket in overview.items()
            },
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Overall status: {status}")
        print(format_table(overview))
        if status != "PASS":
            print()
            print("Failed receipts:")
            for kind in sorted(overview):
                for failure in overview[kind].get("failures", []):
                    ts = failure.timestamp.isoformat().replace("+00:00", "Z") if failure.timestamp else "—"
                    print(f"  - [{kind}] {ts} → {failure.path}")
    return 0 if status == "PASS" else 1


__all__ = [
    "cli_status",
    "collect_receipts",
    "status_summary",
]
