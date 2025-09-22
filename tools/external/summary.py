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
REGISTRY_CONFIG_DEFAULT = ROOT / "docs" / "adoption" / "external-feed-registry.config.json"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"

try:  # local import guarded for CLI usage
    from . import registry_update
except ImportError:  # pragma: no cover - during isolated unit tests
    registry_update = None

if registry_update is not None:
    DEFAULT_REGISTRY_PATH = registry_update.DEFAULT_REGISTRY
    RegistryUpdateError = registry_update.RegistryUpdateError
else:  # pragma: no cover - registry helper not available during minimal tests
    DEFAULT_REGISTRY_PATH = ROOT / "docs" / "adoption" / "external-feed-registry.md"

    class RegistryUpdateError(RuntimeError):
        """Raised when registry integration is unavailable."""


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
    parser.add_argument(
        "--registry-config",
        type=Path,
        help="JSON config mapping feed metadata for registry auto-update",
    )
    parser.add_argument(
        "--registry-path",
        type=Path,
        help="Path to the registry markdown (default: docs/adoption/external-feed-registry.md)",
    )
    parser.add_argument(
        "--registry-dry-run",
        action="store_true",
        help="Compute registry updates without writing to disk",
    )
    parser.add_argument(
        "--notes-json",
        type=Path,
        help="Optional JSON file mapping feed_id to operator notes",
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


def _normalise_registry_paths(
    config_path: Path | None,
    registry_path: Path | None,
) -> tuple[Path | None, Path]:
    cfg = config_path
    if cfg is None and REGISTRY_CONFIG_DEFAULT.exists():
        cfg = REGISTRY_CONFIG_DEFAULT
    if cfg is not None and not cfg.is_absolute():
        cfg = (ROOT / cfg).resolve()
    reg = registry_path or DEFAULT_REGISTRY_PATH
    if not reg.is_absolute():
        reg = (ROOT / reg).resolve()
    return cfg, reg


def _load_registry_config(path: Path) -> dict[str, Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SummaryError(f"registry config not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SummaryError(f"registry config is not valid JSON: {path}") from exc
    feeds = data.get("feeds")
    if not isinstance(feeds, dict):
        raise SummaryError("registry config must contain a 'feeds' object")
    return feeds


def _derive_plan_path(meta: Dict[str, Any]) -> tuple[str, str]:
    plan_id = str(meta.get("plan_id", "")).strip() or None
    plan_path = meta.get("plan_path")
    if plan_path is None:
        if plan_id is None:
            raise SummaryError("registry config missing plan_path or plan_id")
        plan_path = f"_plans/{plan_id}.plan.json"
    return plan_path, plan_id


def _derive_key_path(meta: Dict[str, Any]) -> tuple[str, str | None]:
    key_id = str(meta.get("key_id", "")).strip() or None
    key_path = meta.get("key_path")
    if key_path is None:
        if key_id is None:
            raise SummaryError("registry config missing key_path or key_id")
        key_path = f"governance/keys/{key_id}.pub"
    else:
        if key_id is None:
            key_id = Path(key_path).stem
    return key_path, key_id


def _load_notes(notes_path: Path | None) -> dict[str, str]:
    if notes_path is None:
        return {}
    try:
        data = json.loads(notes_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SummaryError(f"notes file not found: {notes_path}") from exc
    except json.JSONDecodeError as exc:
        raise SummaryError(f"notes file is not valid JSON: {notes_path}") from exc
    if not isinstance(data, dict):
        raise SummaryError("notes JSON must be an object mapping feed_id -> note")
    notes: dict[str, str] = {}
    for feed_id, note in data.items():
        if note is None:
            continue
        notes[str(feed_id)] = str(note)
    return notes


def _augment_summary(
    summary: dict[str, Any],
    *,
    threshold_hours: float,
    notes: dict[str, str],
    notes_path: Path | None,
) -> None:
    feeds: Dict[str, Dict[str, Any]] = summary.get("feeds", {})  # type: ignore[assignment]
    for feed_id, info in feeds.items():
        age_seconds = info.get("latest_age_seconds")
        info["latest_age_hours"] = (age_seconds / 3600) if age_seconds is not None else None
        signals: list[str] = []
        if not info.get("latest_receipt"):
            signals.append("no_receipts")
        if info.get("invalid_signatures", 0):
            signals.append("invalid_signature")
        if info.get("stale_count", 0):
            signals.append("stale_count")
        if age_seconds is None:
            signals.append("missing_timestamp")
        elif age_seconds > threshold_hours * 3600:
            signals.append("stale_threshold")

        score = 1.0
        if "no_receipts" in signals:
            score = 0.0
        else:
            if "invalid_signature" in signals:
                score -= 0.5
            if "stale_count" in signals:
                score -= 0.2
            if "stale_threshold" in signals:
                score -= 0.2
        score = max(0.0, min(1.0, round(score, 3)))
        status = "ok" if not signals else ("attention" if score >= 0.5 else "critical")
        info["trust"] = {
            "score": score,
            "status": status,
            "signals": signals,
        }
        if notes and feed_id in notes:
            info["note"] = notes[feed_id]
        elif "note" in info:
            del info["note"]

    if notes_path is not None:
        summary["notes_source"] = str(notes_path)


def _update_registry_from_summary(
    summary: dict[str, Any],
    registry_config: Path | None,
    registry_path: Path,
    summary_path: Path,
    dry_run: bool,
) -> None:
    if registry_config is None or registry_update is None:
        return
    feeds_meta = _load_registry_config(registry_config)
    summary_feeds: Dict[str, Dict[str, Any]] = summary.get("feeds", {})  # type: ignore[assignment]
    for feed_id, meta in feeds_meta.items():
        if not isinstance(meta, dict):
            raise SummaryError(f"registry config for feed '{feed_id}' must be an object")
        feed_info = summary_feeds.get(feed_id)
        if not feed_info:
            continue
        latest_receipt = feed_info.get("latest_receipt")
        if not latest_receipt:
            continue
        steward = meta.get("steward")
        if not steward:
            raise SummaryError(f"registry config missing steward for feed '{feed_id}'")
        plan_path, plan_id = _derive_plan_path(meta)
        key_path, key_id = _derive_key_path(meta)
        try:
            summary_rel = str(summary_path.relative_to(ROOT))
        except ValueError:
            summary_rel = str(summary_path)

        args = argparse.Namespace(
            registry=registry_path,
            feed_id=feed_id,
            steward=steward,
            plan_path=plan_path,
            plan_id=plan_id,
            key_path=key_path,
            key_id=key_id,
            latest_receipt=latest_receipt,
            summary_path=summary_rel,
            dry_run=dry_run,
        )
        assert registry_update is not None  # narrow type for linters
        try:
            row = registry_update.update_registry(args)
        except RegistryUpdateError as exc:
            raise SummaryError(f"failed to update registry for feed '{feed_id}': {exc}") from exc
        action = "registry dry-run" if dry_run else "registry updated"
        print(f"{action}: {row.strip()}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    summary = summarise_receipts(args.threshold_hours, strict=args.strict)
    output_path = Path(args.out) if args.out else DEFAULT_OUTPUT
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    notes_path: Path | None = None
    if args.notes_json:
        notes_path = args.notes_json if args.notes_json.is_absolute() else (ROOT / args.notes_json).resolve()
    notes = _load_notes(notes_path)
    _augment_summary(summary, threshold_hours=args.threshold_hours, notes=notes, notes_path=notes_path)
    write_summary(summary, output_path)
    try:
        rel = output_path.relative_to(ROOT)
    except ValueError:
        rel = output_path
    print(f"external summary: wrote {rel}")
    registry_config, registry_path = _normalise_registry_paths(args.registry_config, args.registry_path)
    _update_registry_from_summary(summary, registry_config, registry_path, output_path, args.registry_dry_run)
    if args.strict and (summary["invalid_receipts"] or any(f["invalid_signatures"] for f in summary["feeds"].values())):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
