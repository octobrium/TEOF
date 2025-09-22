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
