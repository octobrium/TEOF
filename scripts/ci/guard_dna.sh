#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, os, sys, pathlib

repo = pathlib.Path(".").resolve()
lockp = repo/"governance"/"dna.lock.json"
def fail(msg): print("❌", msg); sys.exit(1)
if not lockp.exists():
    fail("governance/dna.lock.json missing (run DNA lock generator).")
lock = json.loads(lockp.read_text())

# 1) top-level allowlist
top = set(p.name for p in repo.iterdir() if p.name not in {".git","_apoptosis","_report",".bak"})
allow = set(lock["top_level_allowlist"])
extra = sorted(top - allow)
if extra:
    fail(f"unexpected top-level entries: {extra}")

# 2) canonical dirs
for d in lock["canonical_dirs"]:
    if not (repo/d).exists():
        fail(f"missing canonical dir: {d}")

# 3) scripts buckets
for d in lock["scripts_buckets"]:
    if not (repo/d).exists():
        fail(f"missing scripts bucket: {d}")

# 4) single canonical extensions tree
dupes = [str(p) for p in repo.rglob("*/extensions/*") if not str(p).startswith(str(repo/'extensions'))]
if dupes:
    fail(f"found secondary 'extensions/' trees: {dupes[:5]}...")

# 5) capsule/current symlink + freeze artifacts
caps = lock["capsule"]
cur = caps.get("current")
if not cur or cur == "(NOT_A_SYMLINK)":
    fail("capsule/current must be a symlink to a version (e.g., v1.6).")
verdir = repo/"capsule"/cur
for f in ["count","files","root"]:
    if not (verdir/f).exists():
        fail(f"missing freeze artifact: capsule/{cur}/{f}")

# Optional: verify root hash inside lock matches file (if present)
file_root = (verdir/"root").read_text().strip()
lock_root = caps.get("root")
if lock_root and lock_root != file_root:
    fail(f"capsule root mismatch: lock={lock_root} file={file_root}")

print("✅ DNA guard OK")
PY
