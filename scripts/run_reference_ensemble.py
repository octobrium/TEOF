#!/usr/bin/env python3
import glob, json, os, pathlib
from extensions.validator.scorers.ensemble import score_file

IN = "datasets/reference/inputs"
OUT = "datasets/reference/results_ensemble"
pathlib.Path(OUT).mkdir(parents=True, exist_ok=True)

for p in sorted(glob.glob(os.path.join(IN,"*.txt"))):
    res = score_file(p, which=("H",), weights=None)
    base = pathlib.Path(p).stem
    with open(f"{OUT}/{base}.ensemble.json","w",encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"scored {base}: {res['ensemble']}")

print(f"→ wrote {OUT}/*.ensemble.json")
