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
DEFAULT_FEEDBACK_OUTPUT = ROOT / "_report" / "usage" / "external-feedback.json"
AUTHENTICITY_WEIGHTS = {
    "primary_truth": 1.0,
    "source": 0.95,
    "curated": 0.9,
    "synthesis": 0.75,
    "experimental": 0.5,
    "unassigned": 0.8,
}
REGISTRY_CONFIG_DEFAULT = ROOT / "docs" / "adoption" / "external-feed-registry.config.json"
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"

try:  # local import guarded for CLI usage
    from . import registry_update
except ImportError:  # pragma: no cover - during isolated unit tests
    registry_update = None

try:  # optional bus alerting
    from tools.agent import bus_event as bus_event_module
except ImportError:  # pragma: no cover - optional dependency
    bus_event_module = None

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
    parser.add_argument(
        "--feedback-out",
        type=Path,
        help="Optional feedback ledger path (default: _report/usage/external-feedback.json)",
    )
    parser.add_argument(
        "--auth-alert-threshold",
        type=float,
        default=0.6,
        help="Emit a bus status alert when a tier average trust drops below this value (0 disables)",
    )
    parser.add_argument(
        "--disable-auth-alert",
        action="store_true",
        help="Disable authenticity bus alerts",
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


def _build_feed_profiles(feeds_meta: Dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not feeds_meta:
        return {}
    profiles: dict[str, dict[str, Any]] = {}
    for feed_id, meta in feeds_meta.items():
        if not isinstance(meta, dict):
            continue
        steward_label = meta.get("steward")
        profile_raw = meta.get("steward_profile") or {}
        if not isinstance(profile_raw, dict):
            profile_raw = {}
        authenticity = (profile_raw.get("authenticity") or meta.get("authenticity") or "unassigned").strip().lower().replace(" ", "_")
        authenticity_weight = AUTHENTICITY_WEIGHTS.get(authenticity, AUTHENTICITY_WEIGHTS["unassigned"])
        profile = {
            "id": profile_raw.get("id"),
            "label": steward_label,
            "display_name": profile_raw.get("display_name", steward_label),
            "capabilities": profile_raw.get("capabilities", []),
            "obligations": profile_raw.get("obligations", []),
            "trust_baseline": profile_raw.get("trust_baseline", 1.0),
            "contact": profile_raw.get("contact"),
            "notes": profile_raw.get("notes"),
            "authenticity": authenticity,
            "authenticity_weight": authenticity_weight,
        }
        profiles[feed_id] = profile
    return profiles


def _augment_summary(
    summary: dict[str, Any],
    *,
    threshold_hours: float,
    notes: dict[str, str],
    notes_path: Path | None,
    feed_profiles: dict[str, dict[str, Any]],
) -> None:
    feeds: Dict[str, Dict[str, Any]] = summary.get("feeds", {})  # type: ignore[assignment]
    steward_index: dict[str | None, dict[str, Any]] = {}
    authenticity_index: dict[str, dict[str, Any]] = {}
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
        profile = feed_profiles.get(feed_id)
        baseline = float((profile.get("trust_baseline") if profile else 1.0) or 1.0)
        authenticity = (profile.get("authenticity") if profile else "unassigned") or "unassigned"
        tier_weight = float((profile.get("authenticity_weight") if profile else AUTHENTICITY_WEIGHTS.get(authenticity)) or AUTHENTICITY_WEIGHTS["unassigned"])
        info["authenticity"] = {
            "tier": authenticity,
            "weight": round(tier_weight, 3),
        }
        info["trust"]["baseline"] = round(baseline, 3)
        info["trust"]["tier_weight"] = round(tier_weight, 3)
        adjusted = max(0.0, min(1.0, round(score * baseline * tier_weight, 3)))
        info["trust"]["adjusted"] = adjusted

        auth_record = authenticity_index.setdefault(
            authenticity,
            {
                "weight": round(tier_weight, 3),
                "feeds": [],
                "count": 0,
            },
        )
        auth_record["feeds"].append(
            {
                "feed_id": feed_id,
                "trust_adjusted": adjusted,
                "steward_id": profile.get("id") if profile else None,
                "status": info["trust"]["status"],
            }
        )
        auth_record["count"] += 1

        if profile:
            info["steward"] = profile
            steward_id = profile.get("id") or feed_id
            record = steward_index.setdefault(
                steward_id,
                {
                    "id": profile.get("id") or steward_id,
                    "label": profile.get("label"),
                    "display_name": profile.get("display_name") or profile.get("label"),
                    "capabilities": profile.get("capabilities", []),
                    "obligations": profile.get("obligations", []),
                    "trust_baseline": round(baseline, 3),
                    "contact": profile.get("contact"),
                    "notes": profile.get("notes"),
                    "feeds": [],
                },
            )
            record["feeds"].append(
                {
                    "feed_id": feed_id,
                    "trust_adjusted": adjusted,
                    "latest_receipt": info.get("latest_receipt"),
                    "status": info["trust"]["status"],
                }
            )
        if notes and feed_id in notes:
            info["note"] = notes[feed_id]
        elif "note" in info:
            del info["note"]

    if notes_path is not None:
        summary["notes_source"] = str(notes_path)
    if steward_index:
        summary["stewards"] = steward_index
    if authenticity_index:
        summary["authenticity"] = authenticity_index


def _update_registry_from_summary(
    summary: dict[str, Any],
    registry_config: Path | None,
    registry_path: Path,
    summary_path: Path,
    dry_run: bool,
    feeds_meta: Dict[str, Any] | None = None,
) -> None:
    if registry_config is None or registry_update is None:
        return
    feeds_meta = feeds_meta or _load_registry_config(registry_config)
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


def _write_feedback(summary: dict[str, Any], output_path: Path) -> dict[str, Any] | None:
    entries = []
    feeds: Dict[str, Dict[str, Any]] = summary.get("feeds", {})  # type: ignore[assignment]
    for feed_id, info in feeds.items():
        note = info.get("note")
        if not note:
            continue
        steward = info.get("steward") or {}
        trust = info.get("trust") or {}
        entries.append(
            {
                "feed_id": feed_id,
                "note": note,
                "steward_id": steward.get("id"),
                "steward_label": steward.get("label"),
                "trust_adjusted": trust.get("adjusted", trust.get("score")),
                "trust_status": trust.get("status"),
                "signals": trust.get("signals", []),
            }
        )
    if not entries:
        return None
    payload = {
        "generated_at": summary.get("generated_at"),
        "notes_source": summary.get("notes_source"),
        "entries": entries,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _average(values: Iterable[float]) -> float | None:
    numbers = [float(v) for v in values if isinstance(v, (int, float))]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def _alert_authenticity(summary: dict[str, Any], threshold: float | None) -> None:
    if threshold is None or threshold <= 0:
        return
    if bus_event_module is None:
        return
    authenticity_index = summary.get("authenticity")
    if not isinstance(authenticity_index, dict):
        return

    tier_alerts: list[tuple[str, float]] = []
    attention_feeds: list[tuple[str, str, float | None]] = []
    for tier_name, payload in authenticity_index.items():
        if not isinstance(payload, dict):
            continue
        feeds = payload.get("feeds", [])
        adjusted_values = []
        if isinstance(feeds, list):
            for feed in feeds:
                if isinstance(feed, dict):
                    adjusted_values.append(feed.get("trust_adjusted"))
        avg = payload.get("avg_adjusted_trust")
        if not isinstance(avg, (int, float)):
            avg_calc = _average(adjusted_values)
        else:
            avg_calc = float(avg)
        if avg_calc is not None and avg_calc < threshold:
            tier_alerts.append((tier_name, avg_calc))
        feeds = payload.get("feeds", [])
        if isinstance(feeds, list):
            for feed in feeds:
                if not isinstance(feed, dict):
                    continue
                status = feed.get("status")
                if status and status != "ok":
                    attention_feeds.append(
                        (
                            str(feed.get("feed_id")),
                            tier_name,
                            feed.get("trust_adjusted") if isinstance(feed.get("trust_adjusted"), (int, float)) else None,
                        )
                    )

    if not tier_alerts and not attention_feeds:
        return

    summary_parts: list[str] = []
    if tier_alerts:
        tier_msg = ", ".join(f"{name}<{threshold:.2f}" for name, _ in tier_alerts)
        summary_parts.append(f"tiers {tier_msg}")
    if attention_feeds:
        feed_msg = ", ".join(feed for feed, _, _ in attention_feeds[:5])
        summary_parts.append(f"attention feeds {feed_msg}")
    summary_text = "authenticity alert: " + "; ".join(summary_parts)

    argv = [
        "log",
        "--event",
        "status",
        "--summary",
        summary_text,
        "--agent",
        "teof-auth-monitor",
    ]
    for tier_name, avg in tier_alerts:
        argv.extend(["--extra", f"{tier_name}_avg={avg:.3f}"])
    for feed_id, tier_name, trust in attention_feeds[:5]:
        extras = f"{feed_id}_tier={tier_name}"
        if trust is not None:
            extras += f";trust={trust:.3f}"
        argv.extend(["--extra", extras])
    try:
        bus_event_module.main(argv)
    except Exception:  # pragma: no cover - bus event failures shouldn't break summary
        return


def _suggest_next_step() -> None:
    if bus_event_module is None:
        return
    try:
        from tools.autonomy import next_step as next_step_module
    except ImportError:
        return
    try:
        suggestion = next_step_module.select_next_step(claim=False, allow_failure=True)
    except Exception:
        return
    if not suggestion:
        return
    summary_text = f"next-step suggestion: {suggestion.get('id')} {suggestion.get('title')}"
    argv = [
        "log",
        "--event",
        "status",
        "--summary",
        summary_text,
        "--agent",
        "teof-next-step",
    ]
    if suggestion.get("plan_suggestion"):
        argv.extend(["--extra", f"plan={suggestion['plan_suggestion']}"])
    if suggestion.get("notes"):
        argv.extend(["--extra", f"notes={suggestion['notes']}"])
    try:
        bus_event_module.main(argv)
    except Exception:  # pragma: no cover - bus event failures shouldn't break summary
        return


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
    registry_config, registry_path = _normalise_registry_paths(args.registry_config, args.registry_path)
    feeds_meta: Dict[str, Any] | None = None
    feed_profiles: dict[str, dict[str, Any]] = {}
    if registry_config is not None and registry_config.exists():
        try:
            feeds_meta = _load_registry_config(registry_config)
            feed_profiles = _build_feed_profiles(feeds_meta)
        except SummaryError as exc:
            if args.registry_config:
                raise
            print(f"warning: {exc}")
            feeds_meta = None
            feed_profiles = {}
    _augment_summary(
        summary,
        threshold_hours=args.threshold_hours,
        notes=notes,
        notes_path=notes_path,
        feed_profiles=feed_profiles,
    )
    write_summary(summary, output_path)
    try:
        rel = output_path.relative_to(ROOT)
    except ValueError:
        rel = output_path
    print(f"external summary: wrote {rel}")
    _update_registry_from_summary(
        summary,
        registry_config,
        registry_path,
        output_path,
        args.registry_dry_run,
        feeds_meta=feeds_meta,
    )
    feedback_path = args.feedback_out if args.feedback_out else DEFAULT_FEEDBACK_OUTPUT
    if not feedback_path.is_absolute():
        feedback_path = ROOT / feedback_path
    feedback_payload = _write_feedback(summary, feedback_path)
    try:
        from . import authenticity_report
    except ImportError:
        authenticity_report = None
    if authenticity_report is not None:
        auth_md = authenticity_report.DEFAULT_MARKDOWN
        auth_json = authenticity_report.DEFAULT_JSON
        if not auth_md.is_absolute():
            auth_md = ROOT / auth_md
        if not auth_json.is_absolute():
            auth_json = ROOT / auth_json
        authenticity_report.generate_dashboard(
            summary,
            feedback_payload,
            auth_md,
            auth_json,
        )
        docs_auth_md = ROOT / "docs" / "usage" / "external-authenticity.md"
        docs_auth_md.parent.mkdir(parents=True, exist_ok=True)
        docs_auth_md.write_text(auth_md.read_text(encoding="utf-8"), encoding="utf-8")
    auth_threshold = None if args.disable_auth_alert or args.auth_alert_threshold <= 0 else args.auth_alert_threshold
    _alert_authenticity(summary, auth_threshold)
    _suggest_next_step()
    if args.strict and (summary["invalid_receipts"] or any(f["invalid_signatures"] for f in summary["feeds"].values())):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
