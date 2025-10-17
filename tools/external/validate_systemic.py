#!/usr/bin/env python3
"""Validate systemic receipt envelopes against repo-neutral expectations."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List
import re


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


def validate_file(path: Path) -> List[str]:
    payload = _load_json(path)
    return _validate_receipt(payload, origin=path)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipts", nargs="+", type=Path, help="Path(s) to systemic receipt JSON files.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    all_errors: List[str] = []
    for receipt_path in args.receipts:
        receipt_path = receipt_path.expanduser().resolve()
        if not receipt_path.exists():
            all_errors.append(f"{receipt_path}: file not found")
            continue
        try:
            errors = validate_file(receipt_path)
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
