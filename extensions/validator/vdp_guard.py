"""Volatile Data Protocol enforcement helper.

Provides deterministic checks for structured observations containing
volatile claims. The guard is designed for CI usage so that PRs introducing
volatile data without citations or timestamps fail fast.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, List, Sequence

ISO_Z_SUFFIX = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_FRESH_MINUTES = 10


@dataclass(frozen=True)
class Issue:
    location: str
    message: str


class TimestampError(ValueError):
    """Raised when a timestamp cannot be parsed."""


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise TimestampError("missing timestamp_utc")
    raw = value.strip()
    try:
        return datetime.strptime(raw, ISO_Z_SUFFIX).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise TimestampError(f"invalid timestamp_utc '{raw}'") from exc


def _require_source(value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing source")


def _check_staleness(ts: datetime, *, now: datetime, stale_labeled: bool, window: timedelta) -> Issue | None:
    if now < ts:
        # Future-dated entries are not stale.
        return None
    age = now - ts
    if age <= window:
        return None
    if stale_labeled:
        return None
    minutes = int(window.total_seconds() // 60)
    return Issue(
        location="timestamp_utc",
        message=f"data older than {minutes}m but stale_labeled=false",
    )


def evaluate_observations(
    observations: Sequence[dict[str, Any]] | None,
    *,
    now: datetime | None = None,
    fresh_minutes: int = DEFAULT_FRESH_MINUTES,
) -> tuple[str, List[Issue]]:
    """Assess observations for VDP compliance.

    Returns a verdict ("pass" or "fail") with issue details.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    window = timedelta(minutes=fresh_minutes)
    issues: List[Issue] = []
    if not observations:
        return "pass", issues

    for idx, obs in enumerate(observations):
        if not isinstance(obs, dict):
            issues.append(Issue(location=f"observations[{idx}]", message="expected object"))
            continue
        if not obs.get("volatile"):
            continue
        base_location = f"observations[{idx}]"
        try:
            ts = _parse_timestamp(obs.get("timestamp_utc"))
        except TimestampError as exc:
            issues.append(Issue(location=f"{base_location}.timestamp_utc", message=str(exc)))
            ts = None
        try:
            _require_source(obs.get("source"))
        except ValueError as exc:
            issues.append(Issue(location=f"{base_location}.source", message=str(exc)))
        if ts is not None:
            stale_flag = bool(obs.get("stale_labeled"))
            issue = _check_staleness(ts, now=now, stale_labeled=stale_flag, window=window)
            if issue is not None:
                issues.append(Issue(location=f"{base_location}.{issue.location}", message=issue.message))

    verdict = "fail" if issues else "pass"
    return verdict, issues


def evaluate_payload(payload: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    observations = payload.get("observations") if isinstance(payload, dict) else None
    verdict, issues = evaluate_observations(observations, now=now)
    return {
        "verdict": verdict,
        "issues": [issue.__dict__ for issue in issues],
    }


__all__ = [
    "Issue",
    "evaluate_observations",
    "evaluate_payload",
    "DEFAULT_FRESH_MINUTES",
]
