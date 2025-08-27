#!/usr/bin/env python3
import sys, json, hashlib, time, os
from pathlib import Path

def score_text(txt:str):
    # Minimal, transparent heuristics as placeholders (bounded, explainable)
    s = {}
    s["observation"] = 1 if "What we know" in txt or "Observation" in txt else 0
    s["coherence"]   = 1 if len(txt) < 6000 else 0
    s["evidence"]    = 1 if ("hash" in txt.lower() or "commit" in txt.lower()) else 0
    s["recursion"]   = 1 if "next loop" in txt.lower() or "feedback" in txt.lower() else 0
    s["safety"]      = 1 if "sunset" in txt.lower() or "fallback" in txt.lower() else 0
    s["total"] = sum(s.values())
    s["explain"] = "Heuristic placeholder; replace with learned scorer when receipts exist."
    return s

def main():
    p = Path(sys.argv[1]) if len(sys.argv)>1 else None
    if not p or not p.exists():
        print(json.dumps({"error":"missing input"})); sys.exit(0)
    txt = p.read_text(encoding="utf-8", errors="ignore")
    s = score_text(txt)
    print(json.dumps(s, indent=2))

if __name__ == "__main__":
    main()
