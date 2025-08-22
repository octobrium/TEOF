#!/usr/bin/env python3
import os, sys, json
from pathlib import Path
from datetime import datetime, timezone
from subprocess import run, PIPE

# --- paths ---
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EVAL = ROOT / "tools" / "teof_evaluator.py"
OUT_ROOT = ROOT.parent / "artifacts" / "ocers_out"  # single source of truth for outputs  # single source of truth for outputs

print(f"[TEOF-CLI] running: {__file__}")

# --- fetchers ---
# safe import with local stub fallback
try:
    from scripts import fetchers  # stdlib-only, local
except Exception:
    class _Fetchers:
        @staticmethod
        def fetch_all(*args, **kwargs): return {}
        @staticmethod
        def fetch(*args, **kwargs): return {}
        @staticmethod
        def to_ocers(*args, **kwargs): return {"observations": []}
        def __getattr__(self, name):
            # Satisfy any missing fetch_* symbol (e.g., fetch_btc)
            if name.startswith("fetch_"):
                return (lambda *a, **k: {})
            raise AttributeError(name)
    fetchers = _Fetchers()

FETCHER_MAP = {
    "BTC":  fetchers.fetch_btc,
    "IBIT": fetchers.fetch_ibit,
    "NVDA": fetchers.fetch_nvda,
    "PLTR": fetchers.fetch_pltr,
    "MSTR": fetchers.fetch_mstr,
}

# --- utils ---
def utc_stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def default_config():
    return {
        "mode": "strict",
        "fresh_minutes": 10,
        "assets": ["BTC", "IBIT", "NVDA", "PLTR", "MSTR"],
    }

def load_config():
    yml = ROOT / "config" / "brief.yml"
    jsn = ROOT / "config" / "brief.json"
    try:
        import yaml  # optional
    except Exception:
        yaml = None

    if yml.exists() and yaml is not None:
        with open(yml, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            return {**default_config(), **cfg}
    if jsn.exists():
        with open(jsn, "r", encoding="utf-8") as f:
            cfg = json.load(f) or {}
            return {**default_config(), **cfg}
    return default_config()

def _is_stale(ts, minutes):
    if not ts:
        return True
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return True
    return (datetime.now(timezone.utc) - dt).total_seconds() > (int(minutes) * 60)

def build_ocers(cfg, fresh_minutes):
    fresh_min = int(cfg.get("fresh_minutes", fresh_minutes if fresh_minutes is not None else 10))
    observations = []
    for a in cfg.get("assets", []):
        fn = FETCHER_MAP.get(str(a).upper())
        data = fn() if fn else None
        if data:
            base = dict(data)
            base["label"] = base.get("label") or f"{a} last"
            base["volatile"] = True
            is_stale = _is_stale(base.get("timestamp_utc"), fresh_min)
            already_marked = bool(base.get("stale_labeled"))
            if is_stale and not str(base["label"]).rstrip().endswith("(stale)"):
                base["stale_labeled"] = True
                base["label"] = f'{base["label"].rstrip()} (stale)'
                base["stale_reason"] = f"older than {fresh_min}m"
            elif already_marked:
                base["stale_labeled"] = True
            observations.append(base)
        else:
            observations.append({
                "label": f"{a} last",
                "value": None,
                "timestamp_utc": None,
                "source": None,
                "volatile": True,
                "stale_labeled": False,
                "provenance": f"fetcher failed at {utc_stamp()}",
            })

    return {
        "ocers": {
            "observation": "Daily brief (auto-generated).",
            "coherence": "",
            "evidence": "",
            "result": "If any values are null, use explore mode or fix fetchers.",
            "scope": "Tactical (days-weeks)",
        },
        "observations": observations,
    }

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(data, (dict, list)):
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            f.write(str(data))

def run_evaluator(report_path, mode, fresh_minutes):
    env = os.environ.copy()
    env["TEOF_MODE"] = str(mode)
    env["VDP_FRESH_MINUTES"] = str(int(fresh_minutes))
    p = run(
        [sys.executable, str(EVAL)],
        input=Path(report_path).read_bytes(),
        stdout=PIPE,
        stderr=PIPE,
        env=env,
    )
    return p.returncode, p.stdout.decode(), p.stderr.decode()

def to_markdown(score_text, ocers_json, mode, fresh):
    lines = [
        "# TEOF Brief",
        f"- Mode: {mode}",
        f"- Fresh window (min): {fresh}",
        "",
        "## Score",
        "```",
        score_text.strip(),
        "```",
        "",
        "## Observations",
        "",
        "| label | value | timestamp_utc | source | stale_labeled |",
        "|---|---:|---|---|---|",
    ]
    for o in ocers_json.get("observations", []):
        lines.append(
            f"| {o.get('label')} | {o.get('value')} | {o.get('timestamp_utc')} | "
            f"{o.get('source')} | {o.get('stale_labeled', False)} |"
        )
    return "\n".join(lines)

def update_latest_symlink(outdir: Path):
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    latest = OUT_ROOT / "latest"
    try:
        if latest.exists() or latest.is_symlink():
            latest.unlink()
    except FileNotFoundError:
        pass
    # point to the absolute dir we just wrote
    latest.symlink_to(outdir.resolve())
    print(f">>> latest -> {latest.readlink()}")

def main():
    cfg = load_config()
    mode = str(cfg.get("mode", "strict")).lower()
    fresh = int(cfg.get("fresh_minutes", 10))

    ts = utc_stamp()
    outdir = OUT_ROOT / ts
    outdir.mkdir(parents=True, exist_ok=True)

    ocers = build_ocers(cfg, fresh)
    report_path = outdir / "brief.json"
    write(report_path, ocers)

    rc, out, err = run_evaluator(report_path, mode, fresh)

    if mode == "strict" and rc != 0:
        rc2, out2, err2 = run_evaluator(report_path, "explore", fresh)
        out = out.strip() + "\n\n---\n[auto-fallback] strict failed; explore report below:\n" + out2

    write(outdir / "score.txt", out)
    write(outdir / "brief.md", to_markdown(out, ocers, mode, fresh))

    # Safety check: ensure files exist
    must = [outdir / "brief.json", outdir / "brief.md", outdir / "score.txt"]
    for f in must:
        if not f.exists():
            raise RuntimeError(f"[TEOF-CLI] ERROR: expected output missing: {f}")

    # Atomically update latest symlink, then show directory contents
    update_latest_symlink(outdir)
    print(">>> written files:")
    for f in sorted(outdir.iterdir()):
        print(" -", f.name)

    # Print evaluator output summary then final path (handy for scripts)
    print(out.strip())
    print(f"wrote: {outdir}")

if __name__ == "__main__":
    main()
