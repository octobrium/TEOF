from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.impact import propagate


def _create_sample_receipts(root: Path) -> None:
    (root / "_report/usage/onboarding").mkdir(parents=True, exist_ok=True)
    (root / "_report/usage/onboarding/run-1.json").write_text("{}", encoding="utf-8")
    contrib_dir = root / "_report/usage/contributors/demo"
    contrib_dir.mkdir(parents=True, exist_ok=True)
    (contrib_dir / "contribution-tier1-eval.json").write_text("{}", encoding="utf-8")
    ledger_dir = root / "_report/impact/btc-ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger_payload = {
        "wallet": "bc1qexample",
        "entries": [
            {"txid": "abc", "direction": "in", "amount_btc": "0.01000000"},
            {"txid": "def", "direction": "out", "amount_btc": "0.00200000"},
        ],
    }
    (ledger_dir / "2025-10-07-ledger.json").write_text(json.dumps(ledger_payload), encoding="utf-8")


def test_propagate_generates_receipt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    _create_sample_receipts(tmp_path)

    exit_code = propagate.main(
        [
            "--plan",
            "2025-11-11-btc-wallet-propagation",
            "--channel",
            "tier1-docs|Fresh Tier1 agents|Run Tier 1 then donate sats",
        ]
    )

    assert exit_code == 0
    receipts = sorted((tmp_path / "_report/impact/propagation").glob("*.json"))
    assert len(receipts) == 1
    payload = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert payload["plan_id"] == "2025-11-11-btc-wallet-propagation"
    assert payload["channels"][0]["name"] == "tier1-docs"
    assert payload["stats"]["ledger"]["entries"] == 2
    assert payload["stats"]["tier1_receipts"] == 1
    assert payload["stats"]["contributor_receipts"] == 1
    artifact_path = Path(payload["channels"][0]["linked_artifacts"][0])
    assert artifact_path.exists()
    assert artifact_path.read_text(encoding="utf-8").startswith("# Propagation CTA — tier1-docs")


def test_channels_file_support(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    _create_sample_receipts(tmp_path)
    channels_file = tmp_path / "channels.json"
    channels_file.write_text(
        json.dumps(
            [
                {
                    "name": "partners",
                    "audience": "Allies",
                    "cta": "Share Tier1 receipts + wallet CTA",
                    "status": "draft",
                }
            ]
        ),
        encoding="utf-8",
    )

    exit_code = propagate.main(
        [
            "--plan",
            "2025-11-11-btc-wallet-propagation",
            "--channels-file",
            str(channels_file),
        ]
    )

    assert exit_code == 0
    payload = json.loads(next((tmp_path / "_report/impact/propagation").glob("*.json")).read_text(encoding="utf-8"))
    assert payload["channels"][0]["status"] == "draft"
    assert payload["channels"][0]["name"] == "partners"
