from __future__ import annotations

import json
import re
from pathlib import Path

from tools.external import validate_systemic


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "systemic"
EXAMPLE_PATH = ROOT / "docs" / "examples" / "systemic" / "receipt.sample.json"
SIGNED_PATH = ROOT / "docs" / "examples" / "systemic" / "receipt.signed.json"
KEY_DIR = ROOT / "docs" / "examples" / "systemic" / "keys"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_metadata_schema_required_fields_present() -> None:
    schema = _load(SCHEMA_DIR / "metadata.schema.json")
    systemic = _load(EXAMPLE_PATH)["systemic"]

    required = schema.get("required", [])
    for field in required:
        assert field in systemic, f"missing systemic field: {field}"

    token_pattern = re.compile(r"^S(10|[1-9])$")
    layer_pattern = re.compile(r"^L[0-6]$")

    for token in systemic["systemic_targets"]:
        assert token_pattern.match(token), f"invalid systemic token {token}"
    for token in systemic["layer_targets"]:
        assert layer_pattern.match(token), f"invalid layer token {token}"

    assert systemic["systemic_scale"] == int(systemic["systemic_scale"]), "scale must be integer"
    assert systemic["layer"] in systemic["layer_targets"], "primary layer should appear in layer_targets"


def test_receipt_schema_required_fields_present() -> None:
    schema = _load(SCHEMA_DIR / "receipt.schema.json")
    payload = _load(EXAMPLE_PATH)

    required = schema.get("required", [])
    for field in required:
        assert field in payload, f"receipt missing {field}"

    hash_pattern = re.compile(r"^[a-f0-9]{64}$")
    assert hash_pattern.match(payload["hash_sha256"]), "invalid SHA-256 digest"

    if "signature" in payload:
        assert payload.get("public_key_id"), "signature included without public_key_id"
        assert payload.get("signature_algorithm") == "ed25519", "unexpected signature algorithm"


def test_validate_systemic_receipt_sample_ok() -> None:
    errors = validate_systemic.validate_file(EXAMPLE_PATH)
    assert errors == []


def test_validate_systemic_receipt_detects_missing_fields(tmp_path: Path) -> None:
    payload = _load(EXAMPLE_PATH)
    payload.pop("hash_sha256", None)
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps(payload), encoding="utf-8")
    errors = validate_systemic.validate_file(broken)
    assert any("hash_sha256" in err for err in errors)


def test_validate_signed_receipt_ok() -> None:
    errors = validate_systemic.validate_file(
        SIGNED_PATH,
        verify_signature=True,
        key_dirs=[KEY_DIR],
    )
    assert errors == []


def test_validate_signed_receipt_missing_key(tmp_path: Path) -> None:
    errors = validate_systemic.validate_file(
        SIGNED_PATH,
        verify_signature=True,
        key_dirs=[tmp_path],
    )
    assert any("public key" in err for err in errors)
