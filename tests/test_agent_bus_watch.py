import datetime as dt
from datetime import timezone

import pytest

from tools.agent.bus_watch import (
    BusWatchError,
    event_matches,
    filter_events,
    format_event,
    parse_iso8601,
)


def make_event(ts: str, agent: str = "codex-1", event: str = "status", **extra):
    payload = {
        "ts": ts,
        "agent_id": agent,
        "event": event,
        "summary": extra.get("summary", "status update"),
        "task_id": extra.get("task_id", "QUEUE-001"),
    }
    if "receipts" in extra:
        payload["receipts"] = extra["receipts"]
    return payload


def test_parse_iso8601_accepts_valid_value():
    ts = parse_iso8601("2025-09-17T23:00:00Z")
    assert ts == dt.datetime(2025, 9, 17, 23, 0, 0, tzinfo=timezone.utc)


def test_parse_iso8601_rejects_invalid_value():
    with pytest.raises(BusWatchError):
        parse_iso8601("2025-09-17 23:00")


def test_event_matches_filters_by_since():
    event = make_event("2025-09-17T23:05:00Z")
    since = dt.datetime(2025, 9, 17, 23, 0, 0, tzinfo=timezone.utc)
    assert event_matches(event, since=since, allowed_agents=None, allowed_events=None)

    since = dt.datetime(2025, 9, 17, 23, 10, 0, tzinfo=timezone.utc)
    assert not event_matches(event, since=since, allowed_agents=None, allowed_events=None)


def test_filter_events_by_agent_and_event():
    events = [
        make_event("2025-09-17T23:00:00Z", agent="codex-1", event="handshake"),
        make_event("2025-09-17T23:05:00Z", agent="codex-2", event="status"),
        make_event("2025-09-17T23:10:00Z", agent="codex-2", event="complete"),
    ]
    filtered = filter_events(
        events,
        since=None,
        agents=["codex-2"],
        events_filter=["status", "complete"],
    )
    assert [ev["event"] for ev in filtered] == ["status", "complete"]


def test_format_event_includes_receipts():
    event = make_event(
        "2025-09-17T23:15:00Z",
        receipts=["_report/test.json"],
        summary="added receipt",
    )
    out = format_event(event)
    assert "added receipt" in out
    assert "receipts=_report/test.json" in out


def test_event_matches_invalid_timestamp_skips():
    event = make_event("not-at-time")
    assert not event_matches(event, since=None, allowed_agents=None, allowed_events=None)
