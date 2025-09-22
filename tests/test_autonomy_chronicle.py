from __future__ import annotations

import json
from pathlib import Path

from tools.autonomy import chronicle


def _summary_payload(ts: str, *, adjusted: float, status: str = "ok") -> dict[str, object]:
    return {
        "generated_at": ts,
        "feeds": {
            "demo": {
                "trust": {
                    "adjusted": adjusted,
                    "status": status,
                    "baseline": 0.85,
                },
                "authenticity": {
                    "tier": "primary_truth",
                },
                "steward": {
                    "id": "codex-5",
                },
            }
        },
        "authenticity": {
            "primary_truth": {
                "weight": 1.0,
                "count": 1,
                "avg_adjusted_trust": adjusted,
                "feeds": [
                    {
                        "feed_id": "demo",
                        "status": status,
                        "trust_adjusted": adjusted,
                    }
                ],
            }
        },
    }


def test_record_entry_writes_markdown_and_ledger(tmp_path: Path) -> None:
    chronicle.ROOT = tmp_path  # type: ignore[attr-defined]
    chronicle.DEFAULT_MARKDOWN = tmp_path / "docs" / "usage" / "chronicle.md"  # type: ignore[attr-defined]
    chronicle.DEFAULT_LEDGER_DIR = tmp_path / "_report" / "usage" / "chronicle"  # type: ignore[attr-defined]

    first = _summary_payload("2025-09-22T21:00:00Z", adjusted=0.8, status="attention")
    chronicle.record_entry(first, max_entries=2)

    md_path = chronicle.DEFAULT_MARKDOWN  # type: ignore[attr-defined]
    assert md_path.exists()
    text = md_path.read_text(encoding="utf-8")
    assert "Authenticity Chronicle" in text
    assert "2025-09-22T21:00:00Z" in text

    ledger_dir = chronicle.DEFAULT_LEDGER_DIR  # type: ignore[attr-defined]
    ledger_files = list(ledger_dir.glob("*.json"))
    assert ledger_files
    payload = json.loads(ledger_files[0].read_text(encoding="utf-8"))
    assert payload["feeds"]
    assert payload["tiers"]

    second = _summary_payload("2025-09-23T06:00:00Z", adjusted=0.9)
    third = _summary_payload("2025-09-24T06:00:00Z", adjusted=0.95)
    chronicle.record_entry(second, max_entries=2)
    chronicle.record_entry(third, max_entries=2)

    text_after = md_path.read_text(encoding="utf-8")
    # Only two most recent entries retained
    assert text_after.count("Authenticity Snapshot") == 2
    assert "2025-09-24T06:00:00Z" in text_after
    assert "2025-09-23T06:00:00Z" in text_after
    assert "2025-09-22T21:00:00Z" not in text_after
