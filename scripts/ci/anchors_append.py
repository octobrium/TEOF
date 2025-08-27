#!/usr/bin/env python3
import sys, json, subprocess, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANCH = ROOT/"governance"/"anchors.json"

def sha256(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def die(msg): print(f"❌ anchors-append: {msg}"); sys.exit(1)

def main():
    if len(sys.argv)<2: die("usage: anchors_append.py <event.json>")
    evp = Path(sys.argv[1]).resolve()
    if not ANCH.exists(): die("governance/anchors.json missing")
    if not evp.exists(): die(f"event file missing: {evp}")

    # Read current & HEAD (for prev_content_hash)
    cur_b = ANCH.read_bytes()
    try:
        head_b = subprocess.check_output(["git","show","HEAD:governance/anchors.json"])
    except Exception:
        head_b = cur_b  # initial repository state

    cur = json.loads(cur_b.decode("utf-8"))
    ev  = json.loads(evp.read_text("utf-8"))
    if "events" not in cur or not isinstance(cur["events"], list):
        die("anchors.json invalid (no 'events' list)")
    if "prev_content_hash" not in ev or "ts" not in ev:
        die("event missing 'prev_content_hash' or 'ts'")

    head_hash = sha256(head_b or b"")
    if ev["prev_content_hash"] != head_hash:
        die("prev_content_hash does not match SHA-256(HEAD anchors.json)")

    # monotonic ts
    if cur["events"]:
        last_ts = str(cur["events"][-1].get("ts",""))
        if str(ev["ts"]) < last_ts:
            die(f"non-monotonic ts: {ev['ts']} < {last_ts}")

    # Append at end
    cur["events"].append(ev)
    ANCH.write_text(json.dumps(cur, indent=2) + "\n", encoding="utf-8")
    print("anchors-append: OK (appended to governance/anchors.json)")
