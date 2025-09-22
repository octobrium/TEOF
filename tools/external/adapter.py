"""Generate signed external observation receipts for TEOF."""
from __future__ import annotations

import argparse
import base64
import binascii
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    from nacl import exceptions as nacl_exceptions
    from nacl import signing
except ImportError:  # pragma: no cover - adapter guards fallback when missing
    nacl_exceptions = None
    signing = None

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_DIR = ROOT / "_report" / "external"
KEYS_DIR = ROOT / "governance" / "keys"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


class AdapterError(RuntimeError):
    """Raised when the adapter cannot produce a receipt."""


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed-id", required=True, help="Feed identifier (slug)")
    parser.add_argument("--plan-id", required=True, help="Plan id that authorized the run")
    parser.add_argument("--key", required=True, help="Path to Ed25519 private key (base64)")
    parser.add_argument("--public-key-id", required=True, help="Registered public key id")
    parser.add_argument("--input", required=True, help="Path to JSON observations or envelope metadata")
    parser.add_argument(
        "--out",
        help="Output path (default: _report/external/<feed>/<issued_at>.json)",
    )
    parser.add_argument(
        "--issued-at",
        help="Override issued_at timestamp (ISO8601 UTC). Defaults to current UTC time.",
    )
    parser.add_argument(
        "--meta",
        nargs="*",
        help="Additional key=value metadata to add alongside observations",
    )
    return parser.parse_args(argv)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise AdapterError(f"invalid JSON in {path}: {exc}") from exc


def _normalise_observations(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and "observations" in data:
        obs = data["observations"]
    else:
        obs = data
    if not isinstance(obs, list):
        raise AdapterError("observations must be a list")
    normalised: list[dict[str, Any]] = []
    for idx, item in enumerate(obs):
        if not isinstance(item, dict):
            raise AdapterError(f"observation {idx} must be an object")
        required = {"label", "value", "timestamp_utc", "source"}
        missing = sorted(required - item.keys())
        if missing:
            raise AdapterError(f"observation {idx} missing fields: {', '.join(missing)}")
        entry = dict(item)
        entry.setdefault("volatile", True)
        entry.setdefault("stale_labeled", False)
        if not isinstance(entry["timestamp_utc"], str):
            raise AdapterError(f"observation {idx} timestamp_utc must be a string")
        normalised.append(entry)
    return normalised


def _load_signing_key(path: Path) -> signing.SigningKey:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError as exc:  # pragma: no cover - defensive
        raise AdapterError(f"cannot read key {path}: {exc}") from exc
    try:
        key_bytes = base64.b64decode(raw)
    except (ValueError, binascii.Error) as exc:  # pragma: no cover - defensive
        raise AdapterError(f"key {path} is not base64 encoded") from exc
    if len(key_bytes) != 32:
        raise AdapterError(f"key {path} must be 32 bytes (was {len(key_bytes)})")
    return signing.SigningKey(key_bytes)


def _canonical_body(payload: dict[str, Any]) -> bytes:
    def default(obj: Any) -> Any:  # pragma: no cover - defensive passthrough
        raise TypeError(f"Unsupported type: {type(obj)!r}")

    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=default).encode("utf-8")


def _apply_meta(envelope: dict[str, Any], meta: Iterable[str] | None) -> None:
    if not meta:
        return
    for item in meta:
        key, sep, value = item.partition("=")
        if not sep:
            raise AdapterError(f"meta item '{item}' must be key=value")
        envelope.setdefault("meta", {})[key] = value


def write_receipt(args: argparse.Namespace) -> Path:
    if signing is None or nacl_exceptions is None:
        raise AdapterError("PyNaCl is required; install with `pip install PyNaCl`.")
    feed_id = args.feed_id.strip().lower()
    if not feed_id:
        raise AdapterError("feed id must be non-empty")

    plan_id = args.plan_id.strip()
    if not plan_id:
        raise AdapterError("plan id must be non-empty")

    signing_key = _load_signing_key(Path(args.key))

    input_payload = _load_json(Path(args.input))
    observations = _normalise_observations(input_payload)

    if args.issued_at:
        try:
            issued_at = dt.datetime.strptime(args.issued_at, ISO_FMT).replace(tzinfo=dt.timezone.utc)
        except ValueError as exc:
            raise AdapterError("issued_at must be ISO8601 UTC") from exc
    else:
        issued_at = dt.datetime.now(dt.timezone.utc)

    issued_str = issued_at.strftime(ISO_FMT)

    body = {
        "feed_id": feed_id,
        "plan_id": plan_id,
        "issued_at": issued_str,
        "observations": observations,
    }
    _apply_meta(body, args.meta)

    body_bytes = _canonical_body(body)
    hash_hex = hashlib.sha256(body_bytes).hexdigest()
    signature = signing_key.sign(body_bytes).signature
    signature_b64 = base64.urlsafe_b64encode(signature).decode("ascii")

    envelope = dict(body)
    envelope["hash_sha256"] = hash_hex
    envelope["signature"] = signature_b64
    envelope["public_key_id"] = args.public_key_id.strip()

    if not envelope["public_key_id"]:
        raise AdapterError("public_key_id must be non-empty")

    if args.out:
        output_path = Path(args.out)
    else:
        issued_slug = issued_at.strftime("%Y%m%dT%H%M%SZ")
        output_path = DEFAULT_REPORT_DIR / feed_id / f"{issued_slug}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        output = write_receipt(args)
    except AdapterError as exc:
        raise SystemExit(str(exc))
    print(f"wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
