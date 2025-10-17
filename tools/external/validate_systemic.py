#!/usr/bin/env python3
"""Validate systemic receipt envelopes against repo-neutral expectations."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Sequence
import re
import base64

try:
    from nacl import signing
except ImportError:  # pragma: no cover
    signing = None


ROOT = Path(__file__).resolve().parents[2]


SYSTEMIC_PATTERN = re.compile(r"^S(10|[1-9])$")
LAYER_PATTERN = re.compile(r"^L[0-6]$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")

REQUIRED_RECEIPT_FIELDS = ("artifact", "hash_sha256", "issued_at", "systemic")
REQUIRED_METADATA_FIELDS = ("systemic_targets", "layer_targets", "systemic_scale", "layer")


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc


def _validate_metadata(metadata: dict, *, origin: Path) -> List[str]:
    errors: List[str] = []
    for field in REQUIRED_METADATA_FIELDS:
        if field not in metadata:
            errors.append(f"{origin}: systemic missing required field '{field}'")
    systemic_targets = metadata.get("systemic_targets", [])
    layer_targets = metadata.get("layer_targets", [])

    if not isinstance(systemic_targets, list) or not systemic_targets:
        errors.append(f"{origin}: systemic_targets must be a non-empty array")
    else:
        for token in systemic_targets:
            if not isinstance(token, str) or not SYSTEMIC_PATTERN.match(token):
                errors.append(f"{origin}: invalid systemic token '{token}'")

    if not isinstance(layer_targets, list) or not layer_targets:
        errors.append(f"{origin}: layer_targets must be a non-empty array")
    else:
        for token in layer_targets:
            if not isinstance(token, str) or not LAYER_PATTERN.match(token):
                errors.append(f"{origin}: invalid layer token '{token}'")

    scale = metadata.get("systemic_scale")
    if not isinstance(scale, int) or not 1 <= scale <= 10:
        errors.append(f"{origin}: systemic_scale must be integer 1-10")
    else:
        scale_token = f"S{scale}"
        if scale_token not in systemic_targets:
            errors.append(f"{origin}: systemic_scale {scale} missing from systemic_targets")

    layer = metadata.get("layer")
    if not isinstance(layer, str) or not LAYER_PATTERN.match(layer):
        errors.append(f"{origin}: layer must be L0-L6 token")
    elif layer not in layer_targets:
        errors.append(f"{origin}: primary layer '{layer}' missing from layer_targets")
    return errors


def _validate_receipt(payload: dict, *, origin: Path) -> List[str]:
    errors: List[str] = []
    for field in REQUIRED_RECEIPT_FIELDS:
        if field not in payload:
            errors.append(f"{origin}: missing required field '{field}'")
    if "hash_sha256" in payload and not SHA256_PATTERN.match(str(payload["hash_sha256"])):
        errors.append(f"{origin}: hash_sha256 must be 64 hex characters")
    metadata = payload.get("systemic")
    if isinstance(metadata, dict):
        errors.extend(_validate_metadata(metadata, origin=origin))
    else:
        errors.append(f"{origin}: systemic must be an object with metadata fields")

    if "signature" in payload and not payload.get("public_key_id"):
        errors.append(f"{origin}: signature present without public_key_id")
    return errors


def _load_verify_key(key_id: str, key_dirs: Sequence[Path]) -> signing.VerifyKey | None:
    if signing is None:
        return None
    for directory in key_dirs:
        candidate = directory / f"{key_id}.pub"
        if candidate.exists():
            raw = candidate.read_text(encoding="utf-8").strip()
            try:
                key_bytes = base64.urlsafe_b64decode(raw)
                return signing.VerifyKey(key_bytes)
            except Exception:
                return None
    return None


def _verify_signature_payload(payload: dict, *, origin: Path, key_dirs: Sequence[Path]) -> List[str]:
    errors: List[str] = []
    signature = payload.get("signature")
    key_id = payload.get("public_key_id")
    if not signature or not key_id:
        errors.append(f"{origin}: missing signature/public_key_id")
        return errors
    if signing is None:
        errors.append(f"{origin}: PyNaCl not available for signature verification")
        return errors
    verify_key = _load_verify_key(str(key_id), key_dirs)
    if verify_key is None:
        locations = ",".join(str(p) for p in key_dirs) or "<none>"
        errors.append(f"{origin}: public key '{key_id}' not found in {locations}")
        return errors
    body = {
        k: payload[k]
        for k in payload
        if k not in {"signature", "public_key_id", "signature_algorithm"}
    }
    try:
        sig_bytes = base64.urlsafe_b64decode(signature)
        verify_key.verify(
            json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"),
            sig_bytes,
        )
    except Exception as exc:  # pragma: no cover - signature failure path
        errors.append(f"{origin}: invalid signature ({exc})")
    return errors


def validate_file(path: Path, *, verify_signature: bool = False, key_dirs: Sequence[Path] | None = None) -> List[str]:
    payload = _load_json(path)
    errors = _validate_receipt(payload, origin=path)
    if verify_signature:
        dirs = list(key_dirs or [])
        errors.extend(_verify_signature_payload(payload, origin=path, key_dirs=dirs))
    return errors


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipts", nargs="+", type=Path, help="Path(s) to systemic receipt JSON files.")
    parser.add_argument(
        "--verify-signature",
        action="store_true",
        help="Verify Ed25519 signatures using provided keys.",
    )
    parser.add_argument(
        "--keys-dir",
        action="append",
        type=Path,
        help="Directory containing <key_id>.pub files (repeatable). Defaults to governance/keys when verify is enabled.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    all_errors: List[str] = []
    key_dirs: List[Path] = []
    if args.verify_signature:
        if args.keys_dir:
            key_dirs.extend([d.expanduser().resolve() for d in args.keys_dir])
        else:
            key_dirs.append((ROOT / "governance" / "keys").resolve())

    for receipt_path in args.receipts:
        receipt_path = receipt_path.expanduser().resolve()
        if not receipt_path.exists():
            all_errors.append(f"{receipt_path}: file not found")
            continue
        try:
            errors = validate_file(
                receipt_path,
                verify_signature=args.verify_signature,
                key_dirs=key_dirs,
            )
        except ValueError as exc:
            all_errors.append(str(exc))
            continue
        if errors:
            all_errors.extend(errors)
        else:
            print(f"[ok] {receipt_path}")
    if all_errors:
        for line in all_errors:
            print(f"[error] {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
