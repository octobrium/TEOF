#!/usr/bin/env python3
import os, sys, json
from pathlib import Path
from datetime import datetime, timezone
from subprocess import run, PIPE

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import fetchers

EVAL = ROOT / "tools" / "teof_evaluator.py"

FETCHER_MAP = {
    "BTC":  fetchers.fetch_btc,
    "IBIT": fetchers.fetch_ibit,
    "NVDA": fetchers.fetch_nvda,
    "PLTR": fetchers.fetch_pltr,
    "MSTR": fetchers.fetch_mstr,
}

def utc_stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def default_config():
    return {"mode":"strict","fresh_minutes":10,"assets":["BTC","IBIT","NVDA","PLTR","MSTR"], "fallback": True}

def load_config():
    yml = ROOT / "config" / "brief.yml"
    jsn = ROOT / "config" / "brief.json"
    try:
        import yaml
    except Exception:
        yaml = None
    if yml.exists() and yaml is not None:
        with open(yml, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or default_config()
    if jsn.exists():
        with open(jsn, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_config()

def build_ocers(cfg):
    obs = []
    for a in cfg.get("assets", []):
        f = FETCHER_MAP.get(a.upper())
        data = f() if f else None
        if data:
            obs.append({
                "label": f"{a} last",
                "value": data.get("value"),
                "timestamp_utc": data.get("timestamp_utc"),
                "source": data.get("source"),
                "provenance": data.get("provenance"),
                "volatile": True,
                "stale_labeled": False
            })
        else:
            obs.append({
                "label": f"{a} last",
                "value": None,
                "timestamp_utc": None,
                "source": None,
                "provenance": "missing",
                "volatile": True,
                "stale_labeled": False
            })
    return {
        "ocers": {
            "observation": "Daily brief (auto-generated).",
            "coherence": "",
            "evidence": "",
            "result": "If any values are null, explore mode or env fallbacks will keep the brief flowing.",
            "scope": "Tactical (days-weeks)"
        },
        "observations": obs
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
    env["TEOF_MODE"] = mode
    env["VDP_FRESH_MINUTES"] = str(fresh_minutes)
    p = run(["python3", str(EVAL)], input=Path(report_path).read_bytes(), stdout=PIPE, stderr=PIPE, env=env)
    return p.returncode, p.stdout.decode(), p.stderr.decode()

def _prov_bucket(p):
    if not p: return "missing"
    if p.startswith("auto:"): return "auto"
    if p.startswith("fallback:"): return p
    if str(p).startswith("manual://"): return "fallback:env"
    return "unknown"

def to_markdown(score_text, ocers_json, mode, fresh):
    obs = ocers_json["observations"]
    total = len(obs)
    auto_count = sum(1 for o in obs if _prov_bucket(o.get("provenance")) == "auto")
    fb_env = sum(1 for o in obs if _prov_bucket(o.get("provenance")) == "fallback:env")
    fb_stooq = sum(1 for o in obs if _prov_bucket(o.get("provenance")) == "fallback:stooq")
    missing = sum(1 for o in obs if _prov_bucket(o.get("provenance")) == "missing")
    lines = []
    lines.append("# TEOF Brief")
    lines.append(f"- Mode: {mode}")
    lines.append(f"- Fresh window (min): {fresh}")
    lines.append("")
    lines.append("## Score")
    lines.append("```")
    lines.append(score_text.strip())
    lines.append("```")
    lines.append("")
    lines.append("## Provenance summary")
    lines.append(f"- Total: {total}")
    lines.append(f"- Auto: {auto_count}")
    lines.append(f"- Fallback (stooq): {fb_stooq}")
    lines.append(f"- Fallback (env): {fb_env}")
    lines.append(f"- Missing: {missing}")
    lines.append("")
    lines.append("## Observations")
    lines.append("| label | value | timestamp_utc | source | provenance |")
    lines.append("|---|---:|---|---|---|")
    for o in obs:
        label = o.get("label")
        val = o.get("value")
        ts = o.get("timestamp_utc")
        src = o.get("source")
        prov = o.get("provenance")
        lines.append(f"| {label} | {val} | {ts} | {src} | {prov} |")
    return "\n".join(lines)

def main():
    cfg = load_config()
    mode = cfg.get("mode","strict").lower()
    fresh = int(cfg.get("fresh_minutes", 10))
    allow_fallback = bool(cfg.get("fallback", True))

    ts = utc_stamp()
    outdir = ROOT / "ocers_out" / ts
    outdir.mkdir(parents=True, exist_ok=True)

    report = build_ocers(cfg)
    try:
        from scripts import events as _events
        ev = _events.scan(_events.load_cfg(str(ROOT / "config" / "events.json")))
        if isinstance(ev, list) and ev:
            report.setdefault("observations", []).extend(ev)
    except Exception:
        pass
    report_path = outdir / "brief.json"
    write(report_path, report)

    rc, out, err = run_evaluator(report_path, mode, fresh)
    write(outdir / "score.txt", out)

    if allow_fallback and mode == "strict" and rc != 0:
        rc2, out2, err2 = run_evaluator(report_path, "explore", fresh)
        out = out.rstrip() + "\n---\n[auto-fallback] strict failed; explore report below:\n" + out2
        (outdir / "score.strict.txt").write_text(out)
        (outdir / "score.explore.txt").write_text(out2)

    md = to_markdown(out, report, mode, fresh)
    write(outdir / "brief.md", md)

    print(out.strip())
    latest = ROOT / "ocers_out" / "latest"
    try:
        if latest.exists() or latest.is_symlink():
            latest.unlink()
        latest.symlink_to(outdir, target_is_directory=True)
    except Exception:
        pass
    print(f"wrote: {outdir} (latest -> {outdir.name})")

if __name__ == "__main__":
    main()
