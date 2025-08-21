#!/usr/bin/env python3
"""
Minimal TEOF evaluator enforcing Volatile Data Protocol (VDP).
Input: JSON on stdin, with top-level "observations" list.
Each volatile entry must have value + timestamp_utc + source unless in explore mode.
Outputs OGS and messages. Exit 0 if pass, 1 if fail.
"""
import sys, json, os
from datetime import datetime, timezone

MODE = os.getenv("TEOF_MODE", "strict").lower()        # strict | explore
FRESH_MINUTES = int(os.getenv("VDP_FRESH_MINUTES", "10"))

def is_stale(ts_utc: str, minutes: int = FRESH_MINUTES) -> bool:
    try:
        # support both "...Z" and with tz offset
        ts = ts_utc.replace('Z', '+00:00')
        dt = datetime.fromisoformat(ts)
    except Exception:
        return True
    now = datetime.now(timezone.utc)
    delta = (now - dt)
    return delta.total_seconds() > minutes * 60

def main():
    data = json.load(sys.stdin)

    observations = data.get("observations", [])
    hard_fail = False
    score = 0
    msgs = []

    for i, obs in enumerate(observations):
        volatile = bool(obs.get("volatile", False))
        if not volatile:
            continue

        val = obs.get("value", None)
        ts = obs.get("timestamp_utc", None)
        src = obs.get("source", None)
        stale_labeled = bool(obs.get("stale_labeled", False))

        if val is None or not ts or not src:
            if MODE == "strict":
                msgs.append(f"[FAIL] obs[{i}] missing value/timestamp/source for volatile claim")
                hard_fail = True
            else:
                msgs.append(f"[WARN] obs[{i}] missing value/timestamp/source (explore mode)")
            continue

        if is_stale(ts) and not stale_labeled:
            if MODE == "strict":
                msgs.append(f"[FAIL] obs[{i}] stale without label (>{FRESH_MINUTES}m)")
                hard_fail = True
            else:
                msgs.append(f"[WARN] obs[{i}] stale without label (>{FRESH_MINUTES}m) (explore mode)")
                score -= 1

        # basic credit for fully cited fresh claim
        if not is_stale(ts):
            score += 1

    print(f"OGS: {score}")
    for m in msgs:
        print(m)

    if hard_fail:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
