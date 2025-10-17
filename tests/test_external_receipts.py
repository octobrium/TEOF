import argparse
import base64
import json
from importlib import reload
from pathlib import Path

import pytest

import scripts.ci.check_vdp as check_vdp
from tools.external import adapter

pytest.importorskip("nacl")


def _prepare_module(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "datasets" / "goldens"
    docs_dir = tmp_path / "docs"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    check_vdp.ROOT = tmp_path
    check_vdp.DATASET_DIR = dataset_dir
    check_vdp.TARGET_DIRS = [docs_dir, tmp_path / "datasets"]
    check_vdp.EXTERNAL_DIR = tmp_path / "_report" / "external"
    check_vdp.KEYS_DIR = tmp_path / "governance" / "keys"
    reload(check_vdp)
    check_vdp.ROOT = tmp_path
    check_vdp.DATASET_DIR = dataset_dir
    check_vdp.TARGET_DIRS = [docs_dir, tmp_path / "datasets"]
    check_vdp.EXTERNAL_DIR = tmp_path / "_report" / "external"
    check_vdp.KEYS_DIR = tmp_path / "governance" / "keys"


def _seed_dataset(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "datasets" / "goldens"
    pass_payload = {
        "expected_verdict": "pass",
        "observations": [
            {
                "label": "BTC",
                "value": 1,
                "timestamp_utc": "2099-01-01T00:00:00Z",
                "source": "https://ex/pass",
                "volatile": True,
                "stale_labeled": False,
            }
        ],
    }
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "pass.json").write_text(json.dumps(pass_payload), encoding="utf-8")


@pytest.fixture
def signing_pair():
    from nacl import signing

    key = signing.SigningKey.generate()
    return key, key.verify_key


def test_adapter_produces_signed_receipt(tmp_path: Path, signing_pair):
    signing_key, verify_key = signing_pair
    _prepare_module(tmp_path)
    _seed_dataset(tmp_path)

    feed_id = "geopolitics"
    plan_id = "2025-09-21-vdp-pilot-case-study"
    keys_dir = tmp_path / "governance" / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)

    priv_path = tmp_path / "keys" / "geopolitics.ed25519"
    priv_path.parent.mkdir(parents=True, exist_ok=True)
    priv_path.write_text(base64.b64encode(signing_key.encode()).decode("ascii"), encoding="utf-8")

    pub_path = keys_dir / "feed-geopolitics-2025.pub"
    pub_path.write_text(base64.b64encode(verify_key.encode()).decode("ascii"), encoding="utf-8")

    raw_observations = {
        "observations": [
            {
                "label": "FX:USD-RUB",
                "value": 96.4,
                "timestamp_utc": "2025-09-21T22:00:00Z",
                "source": "https://api.fx.example/usd-rub",
                "volatile": True,
                "stale_labeled": False,
            }
        ]
    }
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(raw_observations), encoding="utf-8")

    adapter.ROOT = tmp_path
    adapter.DEFAULT_REPORT_DIR = tmp_path / "_report" / "external"
    adapter.KEYS_DIR = tmp_path / "governance" / "keys"
    out_path = adapter.write_receipt(
        argparse.Namespace(
            feed_id=feed_id,
            plan_id=plan_id,
            key=str(priv_path),
            public_key_id="feed-geopolitics-2025",
            input=str(input_path),
            out=None,
            issued_at="2025-09-21T22:05:00Z",
            meta=None,
        )
    )
    assert out_path.exists()

    rc = check_vdp.main()
    assert rc == 0


def test_adapter_rejects_bad_signature(tmp_path: Path, signing_pair):
    signing_key, verify_key = signing_pair
    _prepare_module(tmp_path)
    _seed_dataset(tmp_path)

    keys_dir = tmp_path / "governance" / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)

    pub_path = keys_dir / "feed.geopolitics.pub"
    pub_path.write_text(base64.b64encode(verify_key.encode()).decode("ascii"), encoding="utf-8")

    external_dir = tmp_path / "_report" / "external" / "geopolitics"
    external_dir.mkdir(parents=True, exist_ok=True)
    bad_receipt = {
        "feed_id": "geopolitics",
        "plan_id": "plan",
        "issued_at": "2025-09-21T00:00:00Z",
        "observations": [],
        "hash_sha256": "deadbeef",
        "signature": "invalid",
        "public_key_id": "feed.geopolitics",
    }
    (external_dir / "20250921T000000Z.json").write_text(json.dumps(bad_receipt), encoding="utf-8")

    rc = check_vdp.main()
    assert rc == 1
