#!/usr/bin/env python3
"""
Minimal TEOF evaluator enforcing Volatile Data Protocol (VDP).

Input: JSON on stdin with top-level "observations".
For volatile observations:
  - strict mode: require value + timestamp_utc + source
  - explore mode: warn if missing
Freshness:
  - fresh => credit
  - stale + labeled => credit
  - stale + unlabeled => fail (strict) or warn (explore)
Outputs OGS (Observation Grounding Score) and messages.
Exit 0 if pass, 1 if fail.
"""
import sys, json, os
from datetime import datetime, timezone

MODE = os.getenv("TEOF_MODE", "strict").lower()          # "strict" | "explore"
FRESH_MINUTES = int(os.getenv("VDP_FRESH_MINUTES", "10"))

def is_stale(ts_utc: str, minutes: int = FRESH_MINUTES) -> bool:
    try:
        ts = ts_utc.replace('Z', '+00:00')              # tolerate trailing Z
        dt = datetime.fromisoformat(ts)
    except Exception:
        return True
    now = datetime.now(timezone.utc)
    return (now - dt).total_seconds() > minutes * 60

def main():
    data = json.load(sys.stdin)
    observations = data.get("observations", [])

    hard_fail = False
    score = 0
    msgs = []

    for idx, obs in enumerate(observations, 1):
        if not bool(obs.get("volatile", False)):
            continue

        val = obs.get("value")
        ts = obs.get("timestamp_utc")
        src = obs.get("source")
        label = (obs.get("label") or "").lower()
        stale_flag = bool(obs.get("stale_labeled", False))

        # presence checks
        if val is None or not ts or not src:
            if MODE == "strict":
                msgs.append(f"[FAIL] obs[{idx}] missing value/timestamp/source for volatile claim")
                hard_fail = True
            else:
                msgs.append(f"[WARN] obs[{idx}] missing value/timestamp/source (explore mode)")
            continue

        # freshness checks
        stale = is_stale(ts, FRESH_MINUTES)
        labeled_stale = stale_flag or ("stale" in label)

        if stale:
            if labeled_stale:
                msgs.append(f"[PASS] obs[{idx}] stale labeled (> {FRESH_MINUTES}m)")
                score += 1
            else:
                if MODE == "strict":
                    msgs.append(f"[FAIL] obs[{idx}] stale without label (> {FRESH_MINUTES}m)")
                    hard_fail = True
                else:
                    msgs.append(f"[WARN] obs[{idx}] stale without label (> {FRESH_MINUTES}m) (explore mode)")
                    score -= 1
        else:
            msgs.append(f"[PASS] obs[{idx}] fresh")
            score += 1

    print(f"OGS: {score}")
    for m in msgs:
        print(m)

    sys.exit(1 if hard_fail else 0)

if __name__ == "__main__":
    main()
