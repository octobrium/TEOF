import argparse
import base64
import json
from importlib import reload
from pathlib import Path

import pytest

import scripts.ci.check_vdp as check_vdp
from tools.external import adapter, summary

pytest.importorskip("nacl")


def _prepare_environment(tmp_path: Path):
    summary.ROOT = tmp_path
    summary.EXTERNAL_DIR = tmp_path / "_report" / "external"
    summary.KEYS_DIR = tmp_path / "governance" / "keys"
    summary.DEFAULT_OUTPUT = tmp_path / "_report" / "usage" / "external-summary.json"
    summary.REGISTRY_CONFIG_DEFAULT = tmp_path / "docs" / "adoption" / "external-feed-registry.config.json"
    summary.DEFAULT_REGISTRY_PATH = tmp_path / "docs" / "adoption" / "external-feed-registry.md"
    if summary.registry_update is not None:
        summary.registry_update.ROOT = tmp_path
        summary.registry_update.DEFAULT_REGISTRY = summary.DEFAULT_REGISTRY_PATH

    check_vdp.ROOT = tmp_path
    check_vdp.EXTERNAL_DIR = tmp_path / "_report" / "external"
    check_vdp.KEYS_DIR = tmp_path / "governance" / "keys"
    reload(check_vdp)
    check_vdp.ROOT = tmp_path
    check_vdp.EXTERNAL_DIR = tmp_path / "_report" / "external"
    check_vdp.KEYS_DIR = tmp_path / "governance" / "keys"


@pytest.fixture
def signing_pair():
    from nacl import signing

    key = signing.SigningKey.generate()
    return key, key.verify_key


def _write_keypair(tmp_path: Path, signing_pair):
    signing_key, verify_key = signing_pair
    priv_path = tmp_path / "keys" / "feed.ed25519"
    priv_path.parent.mkdir(parents=True, exist_ok=True)
    priv_path.write_text(base64.b64encode(signing_key.encode()).decode("ascii"), encoding="utf-8")

    keys_dir = tmp_path / "governance" / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    pub_path = keys_dir / "feed.sample-2025.pub"
    pub_path.write_text(base64.b64encode(verify_key.encode()).decode("ascii"), encoding="utf-8")
    return priv_path, pub_path


def _write_receipt(tmp_path: Path, signing_pair, issued_at: str):
    priv_path, _ = _write_keypair(tmp_path, signing_pair)
    observations = {
        "observations": [
            {
                "label": "test",
                "value": 1,
                "timestamp_utc": issued_at,
                "source": "https://example.com/test",
                "volatile": True,
                "stale_labeled": False,
            }
        ]
    }
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(observations), encoding="utf-8")

    adapter.ROOT = tmp_path
    adapter.DEFAULT_REPORT_DIR = tmp_path / "_report" / "external"
    adapter.KEYS_DIR = tmp_path / "governance" / "keys"
    adapter.write_receipt(
        argparse.Namespace(
            feed_id="sample",
            plan_id="2025-09-21-automation-governance-upgrade",
            key=str(priv_path),
            public_key_id="feed.sample-2025",
            input=str(input_path),
            out=None,
            issued_at=issued_at,
            meta=None,
        )
    )

    plan_path = tmp_path / "_plans" / "2025-09-21-automation-governance-upgrade.plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps({"plan_id": "2025-09-21-automation-governance-upgrade"}),
        encoding="utf-8",
    )


def test_summary_outputs_metrics(tmp_path: Path, signing_pair):
    _prepare_environment(tmp_path)
    _write_receipt(tmp_path, signing_pair, issued_at="2025-09-21T22:00:00Z")

    summary_path = tmp_path / "summary.json"
    result = summary.summarise_receipts(threshold_hours=48)
    summary.write_summary(result, summary_path)

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "sample" in payload["feeds"]
    feed_info = payload["feeds"]["sample"]
    assert feed_info["receipt_count"] == 1
    assert feed_info["stale_count"] == 0
    assert feed_info["invalid_signatures"] == 0


def test_summary_flags_stale_and_hash(tmp_path: Path, signing_pair):
    _prepare_environment(tmp_path)
    external_dir = tmp_path / "_report" / "external" / "stale"
    external_dir.mkdir(parents=True, exist_ok=True)
    stale_receipt = {
        "feed_id": "stale",
        "plan_id": "plan",
        "issued_at": "2020-01-01T00:00:00Z",
        "observations": [],
        "hash_sha256": "deadbeef",
        "signature": "",
        "public_key_id": "",
    }
    (external_dir / "20200101T000000Z.json").write_text(json.dumps(stale_receipt), encoding="utf-8")

    result = summary.summarise_receipts(threshold_hours=1)
    assert result["feeds"]["stale"]["stale_count"] == 1
    assert any(item["error"] == "hash_mismatch" for item in result["invalid_receipts"])


def test_summary_updates_registry(tmp_path: Path, signing_pair):
    _prepare_environment(tmp_path)
    _write_receipt(tmp_path, signing_pair, issued_at="2025-09-21T22:00:00Z")

    registry_path = summary.DEFAULT_REGISTRY_PATH
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        "# External Feed Registry\n\n"
        "| feed_id | steward | plan_id | key_id | latest_receipt | summary |\n\n",
        encoding="utf-8",
    )

    config_path = summary.REGISTRY_CONFIG_DEFAULT
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "feeds": {
                    "sample": {
                        "steward": "codex-5",
                        "plan_path": "_plans/2025-09-21-automation-governance-upgrade.plan.json",
                        "key_path": "governance/keys/feed.sample-2025.pub",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "_report" / "usage" / "external-summary.json"
    args = [
        "--threshold-hours",
        "48",
        "--out",
        str(output_path),
        "--registry-config",
        str(config_path),
        "--registry-path",
        str(registry_path),
    ]
    summary.main(args)

    row = [line for line in registry_path.read_text(encoding="utf-8").splitlines() if line.startswith("| sample")]
    assert row
    assert "_report/external/sample" in row[0]
    assert "external-summary.json" in row[0]
