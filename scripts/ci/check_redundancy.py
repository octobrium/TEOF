#!/usr/bin/env python3
import os, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IGNORE_DIRS = {".git", ".githooks", "_report", "__pycache__", ".venv"}
def want(p: Path) -> bool:
    parts = p.parts
    return not any(x in IGNORE_DIRS for x in parts)

def main():
    files = []
    for p in ROOT.rglob("*"):
        if p.is_file() and want(p):
            files.append(p)
    buckets = {}
    for f in files:
        buckets.setdefault(f.name, []).append(str(f.relative_to(ROOT)))
    dups = {k:v for k,v in buckets.items() if len(v) > 1}
    print("--- Redundancy scan (warn-only) ---")
    if not dups:
        print("No duplicate basenames detected")
        return
    for k, paths in sorted(dups.items()):
        print(f"DUP: {k}")
        for path in paths:
            print(f"    {path}")
        print("")
