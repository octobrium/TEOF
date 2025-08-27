#!/usr/bin/env python3
import json, sys, subprocess, hashlib, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "governance" / "anchors.json"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def git_show(pathspec: str) -> bytes:
    try:
        out = subprocess.check_output(["git","show",pathspec], cwd=ROOT)
        return out
    except subprocess.CalledProcessError:
        return b""

def fail(msg: str):
    print(f"❌ anchors-guard: {msg}")
    sys.exit(1)

def warn(msg: str):
    print(f"WARN anchors-guard: {msg}")

def load_json_bytes(b: bytes):
    try:
        return json.loads(b.decode("utf-8"))
    except Exception:
        return None

def main():
    if not P.exists():
        print("anchors-guard: governance/anchors.json missing (skip)")
        return

    head_b = git_show("HEAD:governance/anchors.json")
    cur_b = P.read_bytes()

    head_j = load_json_bytes(head_b) if head_b else None
    cur_j  = load_json_bytes(cur_b)
    if cur_j is None or "events" not in cur_j or not isinstance(cur_j["events"], list):
        fail("current anchors.json is invalid or missing 'events' list")

    cur_events = cur_j["events"]
    if head_j is None:
        # No HEAD => first commit or orphan file; require at least one event with fields
        if not cur_events:
            fail("anchors.json has no events")
        for e in cur_events:
            if not isinstance(e, dict) or "ts" not in e or "prev_content_hash" not in e:
                fail("event missing 'ts' or 'prev_content_hash'")
        # Nothing more we can enforce without history
        print("anchors-guard: no HEAD version; basic structure OK")
        return

    head_events = head_j.get("events", [])
    # 1) No truncation
    if len(cur_events) < len(head_events):
        fail(f"events truncated: head={len(head_events)} current={len(cur_events)}")

    # 2) Prefix must be identical (prevents mid-file edits)
    prefix_len = len(head_events)
    if cur_events[:prefix_len] != head_events:
        fail("mid-file edits detected (prefix of events differs from HEAD)")

    # 3) If no new events, OK
    if len(cur_events) == prefix_len:
        print("anchors-guard: OK (no new events)")
        return

    added = cur_events[prefix_len:]
    if len(added) > 1:
        warn(f"{len(added)} events appended in one change; prefer 1 per PR for clean chains")

    # 4) Field checks + monotonic ts
    last_ts = head_events[-1]["ts"] if head_events else None
    for e in added:
        if not isinstance(e, dict) or "ts" not in e or "prev_content_hash" not in e:
            fail("appended event missing 'ts' or 'prev_content_hash'")
        if last_ts is not None and str(e["ts"]) < str(last_ts):
            fail(f"non-monotonic ts: {e['ts']} < {last_ts}")
        last_ts = e["ts"]

    # 5) Chain tip: first appended event must reference HEAD file hash
    head_hash = sha256_bytes(head_b if head_b else b"")
    first_prev = str(added[0].get("prev_content_hash",""))
    if first_prev != head_hash:
        fail("first appended event prev_content_hash does not match SHA-256(HEAD anchors.json)")

    print("anchors-guard: OK (append-only; tip hash valid; monotonic ts)")
    return

if __name__ == "__main__":
    main()
