#!/usr/bin/env python3
import argparse, glob, json, os, pathlib
from extensions.validator.scorers.ensemble import score_file

def main():
    ap = argparse.ArgumentParser(description="TEOF ensemble scorer over a directory of .txt files")
    ap.add_argument("--in", dest="indir", required=True, help="Input directory with .txt files")
    ap.add_argument("--out", dest="outdir", required=True, help="Output directory for *.ensemble.json")
    args = ap.parse_args()

    IN = pathlib.Path(args.indir).resolve()
    OUT = pathlib.Path(args.outdir).resolve()
    OUT.mkdir(parents=True, exist_ok=True)

    for p in sorted(glob.glob(os.path.join(str(IN),"*.txt"))):
        res = score_file(p, which=("H",), weights=None)
        base = pathlib.Path(p).stem
        with open(OUT/f"{base}.ensemble.json","w",encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(f"scored {base}: {res['ensemble']}")
    print(f"→ wrote {OUT}/*.ensemble.json")

if __name__ == "__main__":
    main()
