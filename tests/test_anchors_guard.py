import copy
import json
from pathlib import Path

import pytest

from scripts.ci.check_anchors_guard import AnchorsGuardError, validate_events, sha256_bytes

ROOT = Path(__file__).resolve().parents[1]
ANCHORS = ROOT / "governance" / "anchors.json"


def load_head():
    head_bytes = ANCHORS.read_bytes()
    head_json = json.loads(head_bytes.decode("utf-8"))
    return head_json, head_bytes


def make_event(ts: str, prev_hash: str) -> dict:
    return {
        "ts": ts,
        "by": "automation",
        "note": "append-only guard test event",
        "prev_content_hash": prev_hash,
    }


def test_validate_events_accepts_single_well_formed_append():
    head_json, head_bytes = load_head()
    current = copy.deepcopy(head_json)

    prev = sha256_bytes(head_bytes)
    current["events"].append(make_event("2025-09-17T17:00:00Z", prev))

    msg = validate_events(head_json, current, head_bytes)
    assert "append-only" in msg


def test_validate_events_rejects_missing_prev_hash():
    head_json, head_bytes = load_head()
    current = copy.deepcopy(head_json)

    event = make_event("2025-09-17T17:05:00Z", sha256_bytes(head_bytes))
    del event["prev_content_hash"]
    current["events"].append(event)

    with pytest.raises(AnchorsGuardError):
        validate_events(head_json, current, head_bytes)


def test_validate_events_rejects_multiple_appends():
    head_json, head_bytes = load_head()
    current = copy.deepcopy(head_json)
    prev = sha256_bytes(head_bytes)

    current["events"].append(make_event("2025-09-17T17:10:00Z", prev))
    current["events"].append(make_event("2025-09-17T17:11:00Z", prev))

    with pytest.raises(AnchorsGuardError):
        validate_events(head_json, current, head_bytes)
