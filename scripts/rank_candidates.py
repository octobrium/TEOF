#!/usr/bin/env python3
import argparse, glob, json, os, pathlib
from extensions.validator import teof_ocers_min as val

MODE_WEIGHTS = {
  "generic": {"O":1.0,"C":1.0,"E":1.0,"R":1.0,"S":1.0},
  "news":    {"O":1.2,"C":1.0,"E":1.0,"R":1.2,"S":0.6},
  "research":{"O":1.0,"C":1.1,"E":1.0,"R":1.4,"S":0.8},
  "code":    {"O":0.6,"C":0.8,"E":0.8,"R":1.6,"S":1.2},
  "tweet":   {"O":0.3,"C":0.5,"E":1.2,"R":0.3,"S":0.2}
}

def score_text(text: str):
    t = val.norm_text(text)
    O = val.score_observation(t); C = val.score_coherence(t)
    E = val.score_ethics(t); R = val.score_repro(t); S = val.score_selfrepair(t)
    return {"O":O,"C":C,"E":E,"R":R,"S":S,"total":O+C+E+R+S}

def rank_dir(indir: str, outdir: str, mode: str):
    weights = MODE_WEIGHTS.get(mode, MODE_WEIGHTS["generic"])
    IN = pathlib.Path(indir).resolve()
    OUT = pathlib.Path(outdir).resolve()
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    for p in sorted(glob.glob(os.path.join(str(IN),"*.txt"))):
        name = pathlib.Path(p).stem
        txt  = pathlib.Path(p).read_text(encoding="utf-8", errors="ignore")
        s = score_text(txt)
        wtotal = round(sum(s[k]*weights[k] for k in ["O","C","E","R","S"]), 2)
        rows.append({"name":name, "path":p, "scores":s, "weighted_total":wtotal})

    rows.sort(key=lambda r: r["weighted_total"], reverse=True)

    rep = []
    rep += [f"# TEOF Rank Report — mode={mode}", ""]
    rep += ["| Candidate | O | C | E | R | S | Raw Total | Weighted Total |",
            "|-----------|---|---|---|---|---|-----------|----------------|"]
    for r in rows:
        s = r["scores"]
        rep.append(f"| {r['name']} | {s['O']} | {s['C']} | {s['E']} | {s['R']} | {s['S']} | {s['total']} | {r['weighted_total']} |")
    pathlib.Path(OUT/"rank_report.md").write_text("\n".join(rep), encoding="utf-8")

    json.dump({"mode":mode,"weights":weights,"ranked":rows}, open(OUT/"rank_report.json","w",encoding="utf-8"), indent=2, ensure_ascii=False)

    top = rows[0] if rows else None
    if top:
        print(f"TOP: {top['name']} -> weighted_total={top['weighted_total']}")
        print(f"Report: {OUT/'rank_report.md'}")
    else:
        print("No .txt candidates found.")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--out", dest="outdir", required=True)
    ap.add_argument("--mode", choices=list(MODE_WEIGHTS.keys()), default="generic")
    args = ap.parse_args()
    rank_dir(args.indir, args.outdir, args.mode)

if __name__ == "__main__":
    main()
