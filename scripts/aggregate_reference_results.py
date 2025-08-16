#!/usr/bin/env python3
import json, glob, os, re
IN = "datasets/reference/results"
OUT = "datasets/reference/reference_report.md"

def row_id(name):
    m = re.match(r"(\d+)_", os.path.basename(name))
    return int(m.group(1)) if m else 9999

def read_scores(path):
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
    o = j["ocers"]
    base = os.path.splitext(os.path.basename(path))[0]
    return {
        "id": row_id(base),
        "source": base.split("_", 1)[1].replace("_", " ").title(),
        "O": o["O"], "C": o["C"], "E": o["E"], "R": o["R"], "S": o["S"],
        "total": o["total"], "verdict": o["verdict"].replace("-", " ")
    }

rows = [read_scores(p) for p in glob.glob(os.path.join(IN, "*.json"))]
rows.sort(key=lambda r: r["id"])

# build table markdown
lines = []
lines += ["# TEOF Reference Report (v0.1)", "", "## Overview",
          "This report evaluates the reference texts using the OCERS protocol (Observation, Coherence, Ethics, Reproducibility, Self-Repair).",
          "Scores range 0–5; higher is stronger.", "", "---", "", "## Scores", ""]
lines += ["| ID  | Source | O | C | E | R | S | Total | Verdict |",
          "|-----|--------|---|---|---|---|---|-------|---------|"]
for r in rows:
    lines.append(f"| {r['id']:03d} | {r['source']} | {r['O']} | {r['C']} | {r['E']} | {r['R']} | {r['S']} | {r['total']}/25 | {r['verdict']} |")

lines += ["", "---", "", "## Notes", "- Scores populated from JSON results in `datasets/reference/results/`."]
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"wrote {OUT}")
