#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json, os, sys, pathlib

repo = pathlib.Path(".").resolve()
def fail(msg): print("❌", msg); sys.exit(1)

lockp = repo/"governance"/"dna.lock.json"
if not lockp.exists():
    fail("governance/dna.lock.json missing (run DNA lock generator).")
lock = json.loads(lockp.read_text())

# 1) top-level allowlist (archive/report excluded from check)
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

# 4) single canonical extensions tree; allow inside _apoptosis/ and _report/
dupes = []
for p in repo.rglob("*/extensions/*"):
    rel = str(p.relative_to(repo))
    if rel.startswith("extensions/"):            # canonical
        continue
    if rel.startswith("_apoptosis/"):            # archived
        continue
    if rel.startswith("_report/"):               # tooling/report
        continue
    if "/extensions/" in rel:
        dupes.append(rel)
if dupes:
    fail(f"found secondary 'extensions/' trees outside canon/archive: {dupes[:8]}")

# 5) capsule/current symlink + freeze hash consistency (if locked)
caps = lock.get("capsule", {})
cur = caps.get("current")
link = repo/"capsule"/"current"
if not link.is_symlink():
    fail("capsule/current must be a symlink to a version (e.g. v1.6).")
symlink_target = os.readlink(link)
if not symlink_target:
    fail("capsule/current symlink is empty")
if not cur or cur == "(NOT_A_SYMLINK)":
    cur = symlink_target
verdir = repo/"capsule"/cur
for f in ["count","files","root"]:
    if not (verdir/f).exists():
        fail(f"missing freeze artifact: capsule/{cur}/{f}")
lock_root = caps.get("root")
file_root = (verdir/"root").read_text().strip()
if lock_root and lock_root != file_root:
    fail(f"capsule root mismatch: lock={lock_root} file={file_root}")

version_tag = cur
version_value = cur.lstrip("v")

def require_contains(path, needle, label):
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        fail(f"capsule metadata mismatch: expected '{needle}' in {label}")

for name in ("capsule.txt", "PROVENANCE.md", "RELEASE.md"):
    require_contains(verdir/name, version_tag, f"capsule/{cur}/{name}")

recon_path = verdir/"reconstruction.json"
if recon_path.exists():
    recon = json.loads(recon_path.read_text(encoding="utf-8"))
    recon_version = str(recon.get("version", "")).strip()
    if recon_version != version_value:
        fail(
            "capsule metadata mismatch: reconstruction.json.version="
            f"{recon_version or '<missing>'} expected {version_value}"
        )

print("✅ DNA guard OK")
PY
