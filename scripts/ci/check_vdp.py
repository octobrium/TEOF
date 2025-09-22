#!/usr/bin/env python3
"""CI guard for Volatile Data Protocol compliance."""
from __future__ import annotations

import json
import sys
import base64
import binascii
import hashlib
from pathlib import Path
from typing import Iterable

from extensions.validator import vdp_guard

ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "datasets" / "goldens"
TARGET_DIRS = [ROOT / "docs", ROOT / "datasets"]
EXTERNAL_DIR = ROOT / "_report" / "external"
KEYS_DIR = ROOT / "governance" / "keys"

try:
    from nacl import exceptions as nacl_exceptions
    from nacl import signing
except ImportError:  # pragma: no cover - import guard tested separately
    signing = None
    nacl_exceptions = None


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"::error::{path.relative_to(ROOT)} invalid JSON: {exc}", file=sys.stderr)
        return None


def _is_structured_payload(data: dict | None) -> bool:
    if not isinstance(data, dict):
        return False
    observations = data.get("observations")
    if not isinstance(observations, list):
        return False
    return any(isinstance(item, dict) and item.get("volatile") for item in observations)


def _canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _load_verify_key(key_id: str) -> signing.VerifyKey:
    if signing is None or nacl_exceptions is None:
        raise SystemExit("PyNaCl required for external receipt verification. Install PyNaCl.")
    key_path = KEYS_DIR / f"{key_id}.pub"
    if not key_path.exists():
        raise SystemExit(f"::error::missing public key governance/keys/{key_id}.pub")
    raw = key_path.read_text(encoding="utf-8").strip()
    try:
        key_bytes = base64.b64decode(raw)
    except (ValueError, binascii.Error):  # pragma: no cover - defensive
        raise SystemExit(f"::error::{key_path.relative_to(ROOT)} not base64 encoded")
    if len(key_bytes) != 32:
        raise SystemExit(f"::error::{key_path.relative_to(ROOT)} must be 32 bytes")
    return signing.VerifyKey(key_bytes)


def check_dataset() -> int:
    failures = 0
    if not DATASET_DIR.exists():
        print("::error::datasets/goldens missing", file=sys.stderr)
        return 1

    for path in sorted(DATASET_DIR.glob("*.json")):
        payload = _load_json(path)
        if payload is None:
            failures += 1
            continue
        expected = payload.get("ocers", {}).get("result")
        if expected not in {"pass", "fail"}:
            rel = path.relative_to(ROOT)
            print(f"::error::{rel} missing ocers.result", file=sys.stderr)
            failures += 1
            continue
        result = vdp_guard.evaluate_payload(payload)
        verdict = result["verdict"]
        if verdict != expected:
            rel = path.relative_to(ROOT)
            print(
                f"::error::{rel} expected {expected} but got {verdict}",
                file=sys.stderr,
            )
            failures += 1
    return failures


def iter_target_json() -> Iterable[Path]:
    for base in TARGET_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.json"):
            if path.is_dir():
                continue
            if path.is_relative_to(DATASET_DIR):
                continue
            yield path


def check_repo_payloads() -> int:
    failures = 0
    for path in iter_target_json():
        payload = _load_json(path)
        if payload is None:
            failures += 1
            continue
        if not _is_structured_payload(payload):
            continue
        verdict, issues = vdp_guard.evaluate_observations(payload.get("observations"))
        if verdict == "fail":
            rel = path.relative_to(ROOT)
            for issue in issues:
                print(
                    f"::error::{rel} {issue.location}: {issue.message}",
                    file=sys.stderr,
                )
            failures += 1
    return failures


def check_external_receipts() -> int:
    if EXTERNAL_DIR.exists() and signing is None:
        print("::error::PyNaCl not installed, cannot verify external receipts", file=sys.stderr)
        return 1
    failures = 0
    if not EXTERNAL_DIR.exists():
        return failures
    for path in sorted(EXTERNAL_DIR.rglob("*.json")):
        payload = _load_json(path)
        if payload is None:
            failures += 1
            continue
        required = {"feed_id", "plan_id", "issued_at", "observations", "hash_sha256", "signature", "public_key_id"}
        missing = required - payload.keys()
        if missing:
            for field in sorted(missing):
                print(f"::error::{path.relative_to(ROOT)} missing {field}", file=sys.stderr)
            failures += 1
            continue
        body = {
            k: payload[k]
            for k in payload
            if k not in {"hash_sha256", "signature", "public_key_id"}
        }
        body_bytes = _canonical_bytes(body)
        expected_hash = hashlib.sha256(body_bytes).hexdigest()
        if expected_hash != payload["hash_sha256"]:
            print(
                f"::error::{path.relative_to(ROOT)} hash mismatch expected {expected_hash} got {payload['hash_sha256']}",
                file=sys.stderr,
            )
            failures += 1
            continue
        try:
            verify_key = _load_verify_key(payload["public_key_id"])
        except SystemExit as exc:
            print(str(exc), file=sys.stderr)
            failures += 1
            continue
        try:
            signature_bytes = base64.urlsafe_b64decode(payload["signature"])
        except (ValueError, binascii.Error):
            print(f"::error::{path.relative_to(ROOT)} signature is not base64url", file=sys.stderr)
            failures += 1
            continue
        try:
            verify_key.verify(body_bytes, signature_bytes)
        except nacl_exceptions.BadSignatureError:
            print(f"::error::{path.relative_to(ROOT)} signature verification failed", file=sys.stderr)
            failures += 1
            continue
    return failures


def main() -> int:
    dataset_failures = check_dataset()
    repo_failures = check_repo_payloads()
    external_failures = check_external_receipts()
    total = dataset_failures + repo_failures + external_failures
    return 0 if total == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
