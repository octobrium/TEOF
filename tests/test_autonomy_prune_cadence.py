from __future__ import annotations

import datetime as dt
from pathlib import Path

from tools.autonomy import prune_cadence


def _patch_metrics(monkeypatch, *, module_files: int, receipt_count: int, baseline_modules: int = 4) -> None:
    monkeypatch.setattr(
        prune_cadence.status_report,
        "get_autonomy_footprint",
        lambda root=None: {
            "module_files": module_files,
            "loc": 120,
            "helper_defs": 6,
            "receipt_count": receipt_count,
        },
    )
    monkeypatch.setattr(
        prune_cadence.status_report,
        "get_autonomy_baseline",
        lambda root=None: {"module_files": baseline_modules, "loc": 120, "helper_defs": 6, "receipt_count": 80},
    )


def test_prune_due_when_receipts_exceed_threshold(monkeypatch, tmp_path: Path) -> None:
    _patch_metrics(monkeypatch, module_files=8, receipt_count=200, baseline_modules=8)
    monkeypatch.setattr(prune_cadence, "_load_prune_receipts", lambda root, limit=10: [])
    report = prune_cadence.compute_cadence(root=tmp_path, receipt_threshold=150)
    assert report["prune_due"] is True
    assert any("receipt_count" in reason for reason in report["due_reasons"])


def test_prune_healthy_with_recent_receipt(monkeypatch, tmp_path: Path) -> None:
    _patch_metrics(monkeypatch, module_files=5, receipt_count=90, baseline_modules=5)
    receipt_dir = tmp_path / "_report" / "usage" / "autonomy-prune"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    recent_time = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = receipt_dir / "prune.json"
    path.write_text(
        f'{{"pruned_at": "{recent_time}", "receipt_count": 80}}',
        encoding="utf-8",
    )

    def _loader(root, limit=10):
        return [(path, {"pruned_at": recent_time, "receipt_count": 80})]

    monkeypatch.setattr(prune_cadence, "_load_prune_receipts", _loader)
    report = prune_cadence.compute_cadence(root=tmp_path, interval_days=10, receipt_threshold=120)
    assert report["prune_due"] is False
    assert report["next_deadline"]
