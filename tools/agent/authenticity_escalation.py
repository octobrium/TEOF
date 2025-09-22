"""Escalate recurring authenticity degradations into steward assignments."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Sequence

from tools.agent import task_assign

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUTH_JSON = ROOT / "_report" / "usage" / "external-authenticity.json"
DEFAULT_SUMMARY_JSON = ROOT / "_report" / "usage" / "external-summary.json"
DEFAULT_STATE_PATH = ROOT / "_report" / "agent" / "teof-auth-monitor" / "escalation-state.json"
DEFAULT_RECEIPT_PATH = ROOT / "_report" / "agent" / "teof-auth-monitor" / "escalations.json"


@dataclass
class FeedStatus:
    """Status snapshot for an individual feed inside a tier."""

    feed_id: str
    trust_adjusted: float | None
    status: str | None
    steward_id: str | None


@dataclass
class TierSnapshot:
    """Aggregated authenticity data for a tier."""

    tier: str
    avg_adjusted_trust: float | None
    feeds: list[FeedStatus]


@dataclass
class Escalation:
    """Represents a steward escalation to be raised."""

    tier: str
    steward_id: str
    feed_ids: list[str]
    avg_trust: float | None
    feed_trust: Dict[str, float | None]


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _extract_tiers_from_summary(summary_payload: Mapping[str, Any]) -> list[TierSnapshot]:
    authenticity = summary_payload.get("authenticity")
    snapshots: list[TierSnapshot] = []
    if not isinstance(authenticity, Mapping):
        return snapshots
    for tier_name, payload in authenticity.items():
        if not isinstance(payload, Mapping):
            continue
        tier = str(tier_name)
        feeds_payload = payload.get("feeds", [])
        feeds_list: list[FeedStatus] = []
        trusts: list[float] = []
        if isinstance(feeds_payload, Sequence):
            for feed in feeds_payload:
                if not isinstance(feed, Mapping):
                    continue
                feed_id = str(feed.get("feed_id", "")).strip()
                if not feed_id:
                    continue
                trust = feed.get("trust_adjusted")
                trust_value = float(trust) if isinstance(trust, (int, float)) else None
                if trust_value is not None:
                    trusts.append(trust_value)
                status = feed.get("status")
                status_str = str(status) if isinstance(status, str) else None
                steward = feed.get("steward_id")
                steward_id = str(steward) if isinstance(steward, str) else None
                feeds_list.append(
                    FeedStatus(
                        feed_id=feed_id,
                        trust_adjusted=trust_value,
                        status=status_str,
                        steward_id=steward_id,
                    )
                )
        avg = payload.get("avg_adjusted_trust")
        if not isinstance(avg, (int, float)):
            avg_value = sum(trusts) / len(trusts) if trusts else None
        else:
            avg_value = float(avg)
        snapshots.append(TierSnapshot(tier=tier, avg_adjusted_trust=avg_value, feeds=feeds_list))
    return snapshots


def _load_state(path: Path) -> dict[str, Any]:
    state = _load_json(path)
    if not isinstance(state, dict):
        state = {}
    state.setdefault("tiers", {})
    return state


def _reset_tier_state(entry: MutableMapping[str, Any]) -> None:
    entry["streak"] = 0
    entry["escalated"] = {}


def _format_task_id(prefix: str, tier: str, steward_id: str, now: datetime) -> str:
    slug = tier.upper().replace(" ", "-")
    return f"{prefix}-{slug}-{steward_id}-{now.strftime('%Y%m%d')}"


def _default_assign(
    escalation: Escalation,
    *,
    manager: str,
    plan_id: str | None,
    prefix: str,
    note_template: str,
    auto_claim: bool,
) -> str:
    now = datetime.now(timezone.utc)
    task_id = _format_task_id(prefix, escalation.tier, escalation.steward_id, now)
    feed_parts = ", ".join(
        f"{feed}:{(escalation.feed_trust.get(feed) if escalation.feed_trust.get(feed) is not None else 'unknown')}"
        for feed in escalation.feed_ids
    )
    note = note_template.format(
        tier=escalation.tier,
        avg="{:.3f}".format(escalation.avg_trust) if escalation.avg_trust is not None else "unknown",
        feeds=feed_parts,
    )
    argv = [
        "--task",
        task_id,
        "--engineer",
        escalation.steward_id,
        "--manager",
        manager,
        "--no-auto-claim" if not auto_claim else "--auto-claim",
    ]
    if plan_id:
        argv.extend(["--plan", plan_id])
    argv.extend(["--note", note])
    task_assign.main(argv)
    return task_id


def evaluate_escalations(
    tiers: Iterable[TierSnapshot],
    *,
    threshold: float,
    streak_required: int,
    state: MutableMapping[str, Any],
    assign_callback: Callable[[Escalation], str | None],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    tiers_state: MutableMapping[str, Any] = state.setdefault("tiers", {})  # type: ignore[assignment]
    for snapshot in tiers:
        tier_state = tiers_state.setdefault(snapshot.tier, {})
        streak = int(tier_state.get("streak", 0))
        escalated_map: MutableMapping[str, bool] = tier_state.setdefault("escalated", {})  # type: ignore[assignment]

        below = snapshot.avg_adjusted_trust is not None and snapshot.avg_adjusted_trust < threshold
        if below:
            streak += 1
        else:
            streak = 0
            escalated_map.clear()
        tier_state["streak"] = streak

        if not below or streak < streak_required:
            continue

        impacted: Dict[str, list[FeedStatus]] = {}
        for feed in snapshot.feeds:
            if not feed.steward_id:
                continue
            trust_low = feed.trust_adjusted is not None and feed.trust_adjusted < threshold
            requires_attention = (feed.status or "ok") != "ok"
            if not trust_low and not requires_attention:
                continue
            impacted.setdefault(feed.steward_id, []).append(feed)

        for steward_id, feeds in impacted.items():
            if escalated_map.get(steward_id):
                continue
            escalation = Escalation(
                tier=snapshot.tier,
                steward_id=steward_id,
                feed_ids=[feed.feed_id for feed in feeds],
                avg_trust=snapshot.avg_adjusted_trust,
                feed_trust={feed.feed_id: feed.trust_adjusted for feed in feeds},
            )
            task_id = assign_callback(escalation)
            escalated_map[steward_id] = True
            records.append(
                {
                    "tier": snapshot.tier,
                    "steward_id": steward_id,
                    "feed_ids": escalation.feed_ids,
                    "avg_trust": escalation.avg_trust,
                    "task_id": task_id,
                }
            )

    return records


def process_authenticity(
    *,
    auth_json: Path,
    summary_json: Path | None,
    state_path: Path,
    receipt_path: Path,
    threshold: float,
    streak_required: int,
    manager: str,
    plan_id: str | None,
    task_prefix: str,
    auto_claim: bool,
    dry_run: bool,
) -> dict[str, Any]:
    summary_report = _load_json(summary_json) if summary_json else {}
    tiers = _extract_tiers_from_summary(summary_report)
    state = _load_state(state_path)
    generated_at = _iso_now()

    def assign(escalation: Escalation) -> str | None:
        if dry_run:
            return _format_task_id(task_prefix, escalation.tier, escalation.steward_id, datetime.now(timezone.utc))
        note_template = (
            "Authenticity tier {tier} below threshold for consecutive runs; feeds {feeds} (avg={avg})."
        )
        return _default_assign(
            escalation,
            manager=manager,
            plan_id=plan_id,
            prefix=task_prefix,
            note_template=note_template,
            auto_claim=auto_claim,
        )

    records = evaluate_escalations(
        tiers,
        threshold=threshold,
        streak_required=streak_required,
        state=state,
        assign_callback=assign,
    )

    state["threshold"] = threshold
    state["streak_required"] = streak_required
    state["updated_at"] = generated_at
    _write_json(state_path, state)

    receipt = {
        "generated_at": generated_at,
        "authenticity_report": str(auth_json.relative_to(ROOT)) if auth_json.exists() and auth_json.is_relative_to(ROOT) else (str(auth_json) if auth_json else None),
        "summary_report": str(summary_json.relative_to(ROOT)) if summary_json and summary_json.is_relative_to(ROOT) else (str(summary_json) if summary_json else None),
        "threshold": threshold,
        "streak_required": streak_required,
        "escalations": records,
        "tiers_considered": [
            {
                "tier": snapshot.tier,
                "avg_adjusted_trust": snapshot.avg_adjusted_trust,
                "feed_count": len(snapshot.feeds),
            }
            for snapshot in tiers
        ],
    }
    _write_json(receipt_path, receipt)
    return receipt


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auth-json", type=Path, default=DEFAULT_AUTH_JSON, help="Path to external-authenticity.json")
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON, help="Path to external-summary.json")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH, help="State ledger to persist streaks")
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT_PATH, help="Receipt output path")
    parser.add_argument("--threshold", type=float, default=0.6, help="Trust threshold below which tiers trigger streaks")
    parser.add_argument("--streak", type=int, default=2, help="Consecutive runs required before escalating")
    parser.add_argument("--manager", default="codex-4", help="Manager agent id for assignments")
    parser.add_argument("--plan", help="Optional plan id to associate with assignments")
    parser.add_argument("--task-prefix", default="AUTH", help="Prefix for generated task identifiers")
    parser.add_argument("--auto-claim", action="store_true", help="Automatically claim escalated tasks")
    parser.add_argument("--dry-run", action="store_true", help="Compute escalations without writing assignments")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    auth_json = args.auth_json if args.auth_json.is_absolute() else (ROOT / args.auth_json)
    summary_json = args.summary_json if args.summary_json.is_absolute() else (ROOT / args.summary_json)
    state_path = args.state if args.state.is_absolute() else (ROOT / args.state)
    receipt_path = args.receipt if args.receipt.is_absolute() else (ROOT / args.receipt)
    process_authenticity(
        auth_json=auth_json,
        summary_json=summary_json,
        state_path=state_path,
        receipt_path=receipt_path,
        threshold=args.threshold,
        streak_required=max(1, args.streak),
        manager=args.manager,
        plan_id=args.plan,
        task_prefix=args.task_prefix,
        auto_claim=args.auto_claim,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
