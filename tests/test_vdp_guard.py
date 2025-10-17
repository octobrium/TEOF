import json
from datetime import datetime, timezone
from pathlib import Path

from extensions.validator import vdp_guard

DATASET_DIR = Path("datasets/goldens")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_golden_dataset_matches_verdicts():
    assert DATASET_DIR.is_dir(), "datasets/goldens missing"
    files = sorted(DATASET_DIR.glob("*.json"))
    assert files, "expected golden fixtures"

    for path in files:
        payload = _load(path)
        expected = payload.get("expected_verdict")
        assert expected in {"pass", "fail"}, f"{path} missing expected_verdict"
        result = vdp_guard.evaluate_payload(payload)
        if expected == "pass":
            assert result["verdict"] == "pass"
            assert result["issues"] == []
        else:
            assert result["verdict"] == "fail"
            assert result["issues"], f"expected issues for {path.name}"


def test_staleness_requires_label():
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    obs = [
        {
            "label": "Test",
            "volatile": True,
            "timestamp_utc": "2024-12-31T23:45:00Z",
            "source": "https://ex/stale",
            "stale_labeled": False,
        }
    ]
    verdict, issues = vdp_guard.evaluate_observations(obs, now=now)
    assert verdict == "fail"
    assert any("stale_labeled=false" in issue.message for issue in issues)


def test_future_timestamp_not_flagged():
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    obs = [
        {
            "label": "Future",
            "volatile": True,
            "timestamp_utc": "2025-01-01T00:10:00Z",
            "source": "https://ex/future",
            "stale_labeled": False,
        }
    ]
    verdict, issues = vdp_guard.evaluate_observations(obs, now=now)
    assert verdict == "pass"
    assert issues == []


def test_invalid_observation_structure():
    verdict, issues = vdp_guard.evaluate_observations(["not-a-dict"])
    assert verdict == "fail"
    assert issues[0].location == "observations[0]"
    assert "expected object" in issues[0].message


def test_missing_source_or_timestamp_yields_issues():
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    obs = [
        {
            "label": "Missing pieces",
            "volatile": True,
            "stale_labeled": False,
        }
    ]
    verdict, issues = vdp_guard.evaluate_observations(obs, now=now)
    assert verdict == "fail"
    messages = {issue.message for issue in issues}
    assert any("missing timestamp_utc" in msg for msg in messages)
    assert any("missing source" in msg for msg in messages)
