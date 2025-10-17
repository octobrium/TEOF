#!/usr/bin/env python3
import argparse, json, os, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# ---- Paths ----
ROOT = Path(__file__).resolve().parents[1]
EX_IN = ROOT / "docs" / "examples" / "brief" / "inputs"
OUT_ROOT = Path(os.environ.get("OUT_ROOT", ROOT / "artifacts"))
OCERS_OUT = OUT_ROOT / "ocers_out"
STATUS_MD = ROOT / "docs" / "status.md"
OBJECTIVES_JSON = ROOT / "governance" / "objectives.json"

# ---- Time helpers ----
def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"

# ---- Proc helper ----
def run(cmd, cwd=ROOT):
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(p.stdout + p.stderr)
    return p.returncode, p.stdout, p.stderr

# ---- Artifacts helpers ----
def ensure_latest_symlink(base: Path, newdir: Path):
    base.mkdir(parents=True, exist_ok=True)
    latest = base / "latest"
    try:
        if latest.is_symlink() or latest.exists():
            latest.unlink()
    except FileNotFoundError:
        pass
    latest.symlink_to(newdir.name)

def aggregate(outdir: Path):
    """Create brief.json + score.txt from *.ensemble.json"""
    items = []
    for p in sorted(outdir.glob("*.ensemble.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        e = data["ensemble"]
        items.append({
            "name": p.stem,
            "O": e["O"], "C": e["C"], "E": e["E"], "R": e["R"], "S": e["S"],
            "total": e["total"],
        })
    items.sort(key=lambda x: (-x["total"], x["name"]))
    brief = {
        "generated_at_utc": utc_iso(),
        "num_items": len(items),
        "scores": items,
    }
    (outdir / "brief.json").write_text(json.dumps(brief, indent=2), encoding="utf-8")
    lines = ["name,total,O,C,E,R,S"]
    lines += [f"{i['name']},{i['total']},{i['O']},{i['C']},{i['E']},{i['R']},{i['S']}" for i in items]
    (outdir / "score.txt").write_text("\n".join(lines), encoding="utf-8")

# ---- CLI: brief ----
def cmd_brief(_args):
    stamp = utc_stamp()
    outdir = OCERS_OUT / stamp
    outdir.mkdir(parents=True, exist_ok=True)

    rc, _, _ = run([sys.executable, "-m", "extensions.validator.scorers.ensemble_cli",
                    "--in", str(EX_IN), "--out", str(outdir)])
    if rc != 0:
        return rc

    aggregate(outdir)
    ensure_latest_symlink(OCERS_OUT, outdir)
    print(f"OK → {outdir}")
    print(f"→ artifacts at: {outdir}/brief.json  and  {outdir}/score.txt")
    return 0

# ---- Repo introspection (for status/tasks) ----
def capsule_pointer_str() -> str:
    cur = ROOT / "capsule" / "current"
    if cur.is_symlink():
        return f"{cur} -> {os.readlink(cur)}"
    if cur.exists():
        return f"{cur} (not a symlink)"
    return "capsule/current (missing)"

def pkg_version_str() -> str:
    try:
        # Python 3.8+: importlib.metadata; for 3.10+ it's stdlib
        try:
            from importlib.metadata import version as _version
        except Exception:  # pragma: no cover
            from importlib_metadata import version as _version  # type: ignore
        return _version("teof")
    except Exception:
        return "(not installed)"

def latest_artifacts_state():
    latest = OCERS_OUT / "latest"
    ok = latest.exists() and (latest / "brief.json").exists() and (latest / "score.txt").exists()
    return str(latest), ok

def load_manual_objectives() -> List[Dict[str, Any]]:
    p = OBJECTIVES_JSON
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data.get("objectives"), list):
                return data["objectives"]
        except Exception:
            pass
    return []

def collect_auto_objectives() -> List[Dict[str, Any]]:
    """Heuristic detectors that produce actionable, low-friction tasks."""
    tasks: List[Dict[str, Any]] = []

    # A1) Missing brief artifacts
    latest = OCERS_OUT / "latest"
    if not (latest / "brief.json").exists() or not (latest / "score.txt").exists():
        tasks.append({
            "id": "OBJ-A1",
            "title": "Generate brief artifacts",
            "how": "Run `teof brief` once to create artifacts/systemic_out/latest/{brief.json,score.txt}",
            "status": "todo",
            "priority": 1
        })

    # A2) Placeholder code present in validator modules
    bad_files = []
    base = ROOT / "extensions" / "validator"
    if base.exists():
        for p in base.rglob("*.py"):
            try:
                txt = p.read_text(encoding="utf-8")
                if ("\\u2026" in txt) or ("<" + "TODO" in txt) or ("PASS  # TO" + "DO" in txt):
                    bad_files.append(str(p.relative_to(ROOT)))
            except Exception:
                pass
    if bad_files:
        preview = ", ".join(bad_files[:6]) + (" (+more)" if len(bad_files) > 6 else "")
        tasks.append({
            "id": "OBJ-A2",
            "title": "Replace placeholders in validator modules",
            "details": bad_files,
            "how": f"Remove placeholder tokens from: {preview}",
            "status": "todo",
            "priority": 2
        })

    # A3) Tests folder sanity (at least one golden/smoke test)
    if not (ROOT / "tests").exists():
        tasks.append({
            "id": "OBJ-A3",
            "title": "Add tests/test_brief.py golden check",
            "how": "Create a minimal pytest that runs `teof brief` and compares one golden JSON.",
            "status": "todo",
            "priority": 2
        })

    # A4) Quickstart mentions editable install + CLI
    qf = ROOT / "docs" / "quickstart.md"
    needs_qs = False
    if not qf.exists():
        needs_qs = True
    else:
        try:
            qt = qf.read_text(encoding="utf-8")
            if "pip install -e ." not in qt or "teof brief" not in qt:
                needs_qs = True
        except Exception:
            needs_qs = True
    if needs_qs:
        tasks.append({
            "id": "OBJ-A4",
            "title": "Update docs/quickstart.md with editable install and CLI",
            "how": "Include `pip install -e .` and `teof brief` usage in Quickstart.",
            "status": "todo",
            "priority": 3
        })

    # A5) Pre-commit hook refreshes status.md
    hook = ROOT / ".githooks" / "pre-commit"
    needs_status = True
    if hook.exists():
        try:
            ht = hook.read_text(encoding="utf-8")
            if "teof status" in ht:
                needs_status = False
        except Exception:
            pass
    if needs_status:
        tasks.append({
            "id": "OBJ-A5",
            "title": "Append STATUS refresh to pre-commit",
            "how": "Add `teof status --quiet || true` and `git add docs/status.md || true` to .githooks/pre-commit",
            "status": "todo",
            "priority": 3
        })

    # A6) Capsule pointer should be a symlink
    cur = ROOT / "capsule" / "current"
    if not cur.exists() or not cur.is_symlink():
        tasks.append({
            "id": "OBJ-A6",
            "title": "Normalize capsule/current to a symlink",
            "how": "Run: rm -f capsule/current && ln -s v1.5 capsule/current",
            "status": "todo",
            "priority": 1
        })

    return tasks

def merged_tasks() -> List[Dict[str, Any]]:
    autos = collect_auto_objectives()
    manual = load_manual_objectives()
    by_id: Dict[str, Dict[str, Any]] = {t["id"]: t for t in autos}
    for m in manual:
        mid = m.get("id")
        if not mid:
            continue
        by_id[mid] = {**by_id.get(mid, {}), **m}
    tasks = list(by_id.values())
    # Sort: todo first, then lower priority first, then id
    tasks.sort(key=lambda t: (t.get("status", "todo") != "todo", t.get("priority", 99), t.get("id", "")))
    return tasks

# ---- status.md template ----
STATUS_TEMPLATE = """# TEOF Status ({now})

## Snapshot
- Capsule: {capsule}
- Package: teof {pkg}
- CLI: `teof brief` → writes `artifacts/systemic_out/<UTCSTAMP>/` and updates `artifacts/systemic_out/latest/`
- Artifacts latest: {latest_path} (ready: {latest_ok})

## Auto Objectives (detected)
{auto_block}

## Manual Objectives (optional)
{obj_block}

## Notes
- Keep `capsule/current` as a symlink.
- Python ≥3.9 for local dev.
"""

# ---- CLI: status ----
def cmd_status(args):
    capsule = capsule_pointer_str()
    pkg = pkg_version_str()
    latest_path, latest_ok = latest_artifacts_state()

    # Auto objectives
    auto = merged_tasks()  # merged already includes manual overrides; we still render manual separately below
    # Render autos only (include items with id starting with OBJ-A)
    auto_lines = []
    for t in auto:
        if isinstance(t.get("id"), str) and t["id"].startswith("OBJ-A"):
            line = f"- [{t.get('status','todo')}] {t['id']} — {t.get('title','')}"
            if t.get("how"):
                line += f" — {t['how']}"
            auto_lines.append(line)
    auto_block = "\n".join(auto_lines) if auto_lines else "- (no issues detected)"

    # Manual objectives (if any)
    manual = load_manual_objectives()
    if manual:
        man_lines = []
        for o in manual:
            tid = o.get("id", "-")
            title = o.get("title", "")
            status = o.get("status", "todo")
            man_lines.append(f"- [{status}] {tid} — {title}")
        obj_block = "\n".join(man_lines)
    else:
        obj_block = "- (none listed)"

    STATUS_MD.parent.mkdir(parents=True, exist_ok=True)
    STATUS_MD.write_text(STATUS_TEMPLATE.format(
        now=utc_iso(),
        capsule=capsule,
        pkg=pkg,
        latest_path=latest_path,
        latest_ok="yes" if latest_ok else "no",
        auto_block=auto_block,
        obj_block=obj_block
    ), encoding="utf-8")

    if not args.quiet:
        print(f"Wrote {STATUS_MD}")
    return 0

# ---- CLI: tasks (for agents/LLMs) ----
def cmd_tasks(args):
    tasks = merged_tasks()
    if args.format == "json":
        print(json.dumps(tasks, indent=2))
    else:
        for t in tasks:
            line = f"{t.get('id')} [{t.get('status','todo')}] (p{t.get('priority',9)}): {t.get('title','')}"
            if "how" in t and t["how"]:
                line += f" — {t['how']}"
            print(line)
    return 0

# ---- Main entrypoint ----
def main():
    ap = argparse.ArgumentParser(prog="teof", description="TEOF CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_brief = sub.add_parser("brief", help="Run brief pipeline and write artifacts")
    p_brief.set_defaults(func=cmd_brief)

    p_status = sub.add_parser("status", help="Refresh docs/status.md snapshot/objectives")
    p_status.add_argument("--quiet", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_tasks = sub.add_parser("tasks", help="List actionable tasks for agents")
    p_tasks.add_argument("--format", choices=["text", "json"], default="text")
    p_tasks.set_defaults(func=cmd_tasks)

    args = ap.parse_args()
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
