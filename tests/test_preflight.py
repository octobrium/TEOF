from __future__ import annotations

import json
from pathlib import Path

from tools.autonomy import preflight


def test_gather_snapshot(tmp_path: Path, monkeypatch) -> None:
    auth_path = tmp_path / "auth.json"
    planner_path = tmp_path / "planner.json"
    auth_path.write_text(json.dumps({"overall_avg_trust": 0.8}) + "\n", encoding="utf-8")
    planner_path.write_text(json.dumps({"status": "ok"}) + "\n", encoding="utf-8")

    monkeypatch.setattr(preflight, "AUTH_JSON", auth_path)
    monkeypatch.setattr(preflight, "STATUS_PATH", planner_path)

    monkeypatch.setattr(preflight.objectives_status, "compute_status", lambda window_days: {"window_days": window_days})
    monkeypatch.setattr(preflight.critic, "detect_anomalies", lambda: [{"id": "A"}])
    monkeypatch.setattr(preflight.tms, "detect_conflicts", lambda: [{"id": "B"}])
    monkeypatch.setattr(preflight.ethics_gate, "detect_violations", lambda: [])

    class _FrontierStub:
        def __init__(self, idx: int) -> None:
            self.idx = idx

        def as_dict(self) -> dict[str, int]:
            return {"idx": self.idx}

    monkeypatch.setattr(
        preflight.frontier,
        "compute_frontier",
        lambda limit: [_FrontierStub(i) for i in range(limit)],
    )

    snapshot = preflight.gather_snapshot(frontier_limit=3, objectives_window_days=5.0)
    assert snapshot["authenticity"]["overall_avg_trust"] == 0.8
    assert snapshot["planner_status"]["status"] == "ok"
    assert snapshot["objectives"]["window_days"] == 5.0
    assert len(snapshot["frontier_preview"]) == 3
    assert snapshot["critic_alerts"][0]["id"] == "A"
    assert snapshot["tms_conflicts"][0]["id"] == "B"


def test_preflight_main_writes_receipt(tmp_path: Path, monkeypatch) -> None:
    receipt_dir = tmp_path / "receipts"

    def _stub_snapshot(*_, **__) -> dict[str, object]:
        return {
            "generated_at": "2025-09-27T00:00:00Z",
            "authenticity": {},
            "planner_status": {},
            "objectives": {},
            "frontier_preview": [],
            "critic_alerts": [],
            "tms_conflicts": [],
            "ethics_violations": [],
        }

    monkeypatch.setattr(preflight, "gather_snapshot", _stub_snapshot)
    result = preflight.main(["--out", str(receipt_dir / "preflight.json")])
    assert result == 0
    assert (receipt_dir / "preflight.json").exists()
