"""Summarise external receipt feeds and detect staleness."""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

try:  # optional signature verification
    from nacl import exceptions as nacl_exceptions
    from nacl import signing
except ImportError:  # pragma: no cover - optional dependency
    nacl_exceptions = None
    signing = None

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_DIR = ROOT / "_report" / "external"
KEYS_DIR = ROOT / "governance" / "keys"
DEFAULT_OUTPUT = ROOT / "_report" / "usage" / "external-summary.json"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


class SummaryError(RuntimeError):
    """Raised when external receipts cannot be summarised."""


@dataclass
class FeedStats:
    feed_id: str
    receipt_count: int = 0
    latest_issued_at: dt.datetime | None = None
    latest_path: Path | None = None
    stale_count: int = 0
    invalid_signatures: int = 0

    @property
    def latest_age_seconds(self) -> float | None:
        if self.latest_issued_at is None:
            return None
        return (dt.datetime.now(dt.timezone.utc) - self.latest_issued_at).total_seconds()


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--threshold-hours",
        type=float,
        default=24.0,
        help="Threshold for stale receipts (default: 24h)",
    )
    parser.add_argument(
        "--out",
        help="Write summary JSON to this path (default: _report/usage/external-summary.json)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when signatures or hashes mismatch (default: warn and continue)",
    )
    return parser.parse_args(argv)


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _load_verify_key(key_id: str) -> signing.VerifyKey | None:
    if signing is None:
        return None
    key_path = KEYS_DIR / f"{key_id}.pub"
    if not key_path.exists():
        return None
    raw = key_path.read_text(encoding="utf-8").strip()
    try:
        key_bytes = base64.urlsafe_b64decode(raw)
    except Exception:  # pragma: no cover - defensive
        return None
    if len(key_bytes) != 32:
        return None
    return signing.VerifyKey(key_bytes)


def _iter_receipts() -> Iterable[Path]:
    if not EXTERNAL_DIR.exists():
        return []
    return sorted(EXTERNAL_DIR.rglob("*.json"))


def summarise_receipts(threshold_hours: float, strict: bool = False) -> dict[str, Any]:
    threshold = dt.timedelta(hours=threshold_hours)
    feeds: Dict[str, FeedStats] = {}
    invalid_receipts: list[dict[str, Any]] = []

    for path in _iter_receipts():
        payload = _load_json(path)
        if payload is None:
            invalid_receipts.append({"path": str(path.relative_to(ROOT)), "error": "invalid_json"})
            continue
        feed_id = str(payload.get("feed_id", "")).strip()
        if not feed_id:
            invalid_receipts.append({"path": str(path.relative_to(ROOT)), "error": "missing_feed_id"})
            continue
        stats = feeds.setdefault(feed_id, FeedStats(feed_id=feed_id))
        stats.receipt_count += 1

        try:
            issued_at = dt.datetime.strptime(payload["issued_at"], ISO_FMT).replace(tzinfo=dt.timezone.utc)
        except Exception:
            invalid_receipts.append({"path": str(path.relative_to(ROOT)), "error": "invalid_issued_at"})
            continue

        if stats.latest_issued_at is None or issued_at > stats.latest_issued_at:
            stats.latest_issued_at = issued_at
            stats.latest_path = path

        if dt.datetime.now(dt.timezone.utc) - issued_at > threshold:
            stats.stale_count += 1

        # Validate hash
        body = {
            k: payload[k]
            for k in payload
            if k not in {"hash_sha256", "signature", "public_key_id"}
        }
        body_bytes = _canonical_bytes(body)
        expected_hash = hashlib.sha256(body_bytes).hexdigest()
        if payload.get("hash_sha256") != expected_hash:
            invalid_receipts.append({
                "path": str(path.relative_to(ROOT)),
                "error": "hash_mismatch",
            })
            if strict:
                stats.invalid_signatures += 1
            continue

        # Verify signature when possible
        signature = payload.get("signature")
        key_id = payload.get("public_key_id")
        if signing is not None and signature and key_id:
            try:
                sig_bytes = base64.urlsafe_b64decode(signature)
            except Exception:
                stats.invalid_signatures += 1
                invalid_receipts.append({
                    "path": str(path.relative_to(ROOT)),
                    "error": "signature_not_base64",
                })
                continue
            verify_key = _load_verify_key(key_id)
            if verify_key is None:
                invalid_receipts.append({
                    "path": str(path.relative_to(ROOT)),
                    "error": "missing_public_key",
                })
                stats.invalid_signatures += 1
                continue
            try:
                verify_key.verify(body_bytes, sig_bytes)
            except nacl_exceptions.BadSignatureError:  # pragma: no cover - verified in tests
                stats.invalid_signatures += 1
                invalid_receipts.append({
                    "path": str(path.relative_to(ROOT)),
                    "error": "signature_invalid",
                })
                continue

    summary = {
        "generated_at": dt.datetime.utcnow().strftime(ISO_FMT),
        "threshold_hours": threshold_hours,
        "feeds": {},
        "invalid_receipts": invalid_receipts,
    }

    for feed_id, stats in sorted(feeds.items()):
        summary["feeds"][feed_id] = {
            "receipt_count": stats.receipt_count,
            "latest_issued_at": stats.latest_issued_at.strftime(ISO_FMT) if stats.latest_issued_at else None,
            "latest_receipt": str(stats.latest_path.relative_to(ROOT)) if stats.latest_path else None,
            "stale_count": stats.stale_count,
            "invalid_signatures": stats.invalid_signatures,
            "latest_age_seconds": stats.latest_age_seconds,
        }

    return summary


def write_summary(summary: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    summary = summarise_receipts(args.threshold_hours, strict=args.strict)
    output_path = Path(args.out) if args.out else DEFAULT_OUTPUT
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    write_summary(summary, output_path)
    try:
        rel = output_path.relative_to(ROOT)
    except ValueError:
        rel = output_path
    print(f"external summary: wrote {rel}")
    if args.strict and (summary["invalid_receipts"] or any(f["invalid_signatures"] for f in summary["feeds"].values())):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
