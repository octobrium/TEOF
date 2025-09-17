#!/usr/bin/env python3
import os, sys, json, hashlib
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

def walk(dirpath: Path):
    for root, _, files in os.walk(dirpath):
        for name in files:
            p = Path(root)/name
            rel = p.relative_to(dirpath).as_posix()
            yield rel, p

def main():
    if len(sys.argv) < 2:
        print("usage: make_hashes.py <dir>"); sys.exit(1)
    root = Path(sys.argv[1]).resolve()
    if not root.exists() or not root.is_dir():
        print(f"not a dir: {root}"); sys.exit(1)

    items = []
    for rel, p in walk(root):
        # ignore obvious noise
        if rel.startswith(".DS_Store"): continue
        if rel == "hashes.json":
            continue
        items.append((rel, sha256_file(p)))

    items.sort(key=lambda x: x[0])
    data = {"root": root.name, "count": len(items),
            "files": [{ "path": k, "sha256": v } for k,v in items]}

    print(json.dumps(data, indent=2, ensure_ascii=False))
if __name__ == "__main__":
    main()
