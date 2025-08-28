#!/usr/bin/env python3
import sys, json, re
from pathlib import Path

WEIGHTS = dict(observation=2, coherence=2, evidence=2, recursion=2, safety=2)  # total 10

def has_any(txt, words):
    t = txt.lower()
    return any(w.lower() in t for w in words)

def observation_score(txt):
    # Mentions of explicit observation blocks, STATUS, or measurable targets
    return 1 if has_any(txt, ["observation", "what we know", "status", "metrics"]) else 0 \
         + 1 if has_any(txt, ["acceptance", "how to test", "deterministic"]) else 0

def coherence_score(txt):
    # Presence of structure and bounded size
    pts = 0
    if re.search(r'(?mi)^#\s|\bgoal:|\bacceptance:', txt): pts += 1
    if len(txt) <= 8000: pts += 1
    return pts

def evidence_score(txt):
    # Hashes/commits/files/code blocks indicate evidence-bearing changes
    pts = 0
    if has_any(txt, ["hash", "sha-256", "commit", "anchors.json", "docs/status.md", "capsule/current"]): pts += 1
    if "```" in txt or re.search(r'(?m)^```', txt): pts += 1
    return pts

def recursion_score(txt):
    # Mentions of loops, ledger, receipts, feedback, OCERS
    return 1 if has_any(txt, ["loop", "feedback", "ledger", "receipts", "ocers"]) else 0 \
         + 1 if has_any(txt, ["next batch", "next loop", "dry-run", "score"]) else 0

def safety_score(txt):
    # Sunset/fallback/sandbox/warn-only & no auto-merge claims
    pts = 0
    if has_any(txt, ["sunset", "fallback", "warn-only", "sandbox", "dry-run"]): pts += 1
    if not has_any(txt, ["auto-merge", "force-push"]): pts += 1
    return pts

SCORERS = dict(
    observation=observation_score,
    coherence=coherence_score,
    evidence=evidence_score,
    recursion=recursion_score,
    safety=safety_score,
)

def score_text(txt: str):
    subs = {k: max(0, min(2, SCORERS[k](txt))) for k in SCORERS}
    total = sum(WEIGHTS[k] * (subs[k] / 2) for k in SCORERS)  # 0..10 in steps of 1
    # keep integer for downstream simplicity
    total_int = int(round(total))
    return dict(subscores=subs, weights=WEIGHTS, total=total_int,
                explain="OCERS v0.2: weighted, deterministic heuristics")

def main():
    p = Path(sys.argv[1]) if len(sys.argv)>1 else None
    if not p or not p.exists():
      print(json.dumps({"error":"missing input"})); return
    txt = p.read_text(encoding="utf-8", errors="ignore")
    print(json.dumps(score_text(txt), indent=2))

if __name__ == "__main__":
    main()
