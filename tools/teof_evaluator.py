#!/usr/bin/env python3
"""Minimal TEOF evaluator stub enforcing Volatile Data Protocol.
Input: JSON with an `observations` list of objects; each volatile entry must have value, timestamp_utc, and source.
Exit: 0 if pass, 1 if fail; prints score and messages.
"""
import sys, json, datetime

FRESH_MINUTES = 10

def is_stale(ts_utc: str, minutes: int = FRESH_MINUTES) -> bool:
    try:
        dt = datetime.datetime.fromisoformat(ts_utc.replace('Z','+00:00'))
    except Exception:
        return True
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    return (now - dt).total_seconds() > minutes * 60

def main():
    data = json.load(sys.stdin)
    observations = data.get('observations', [])
    messages = []
    score = 0
    hard_fail = False

    for i, obs in enumerate(observations):
        volatile = bool(obs.get('volatile', True))
        if not volatile:
            continue
        val = obs.get('value')
        ts = obs.get('timestamp_utc')
        src = obs.get('source')
        if val is None or not ts or not src:
            messages.append(f"[FAIL] obs[{i}] missing value/timestamp/source for volatile claim")
            hard_fail = True
            continue
        # freshness
        if is_stale(ts):
            if not obs.get('stale_labeled', False):
                messages.append(f"[PENALTY] obs[{i}] stale without label (>{FRESH_MINUTES}m)")
                score -= 3
        # basic source check
        score += 1  # reward presence
    if hard_fail:
        print("OGS: 0\n" + "\n".join(messages))
        sys.exit(1)
    print(f"OGS: {max(score,0)}\n" + "\n".join(messages))
    sys.exit(0 if score >= 0 else 1)

if __name__ == '__main__':
    main()
