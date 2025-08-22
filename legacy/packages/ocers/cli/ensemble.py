import argparse
import json
import os
import sys
from glob import glob

WEIGHTS = {"O": 3, "C": 2, "E": 2, "R": 1, "S": 1}
REQUIRED = tuple(WEIGHTS.keys())


def _is_nonempty_text(v):
    return isinstance(v, str) and v.strip() != ""


def _validate_shape(d):
    missing = [k for k in REQUIRED if k not in d]
    empty = [k for k in REQUIRED if k in d and not _is_nonempty_text(d[k])]
    ok = not missing and not empty
    return {"ok": ok, "missing": missing, "empty": empty}


def _score_for_h(d):
    by = {}
    for k, w in WEIGHTS.items():
        by[k] = float(w) if _is_nonempty_text(d.get(k, "")) else 0.0
    by["name"] = "H"
    total = float(sum(v for k, v in by.items() if isinstance(v, (int, float))))
    return by, total


def _process_file(fp, outdir):
    with open(fp, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            return {
                "file": fp,
                "ok": False,
                "error": f"invalid_json: {e}",
                "written": None,
            }

    shape = _validate_shape(data)

    by_h, total = _score_for_h(data)
    perfile = {
        "by_scorer": [by_h],
        "ensemble": {
            "O": by_h["O"],
            "C": by_h["C"],
            "E": by_h["E"],
            "R": by_h["R"],
            "S": by_h["S"],
            "total": total,
        },
    }

    base = os.path.splitext(os.path.basename(fp))[0]
    outfp = os.path.join(outdir, f"{base}.ensemble.json")
    os.makedirs(outdir, exist_ok=True)
    with open(outfp, "w", encoding="utf-8") as w:
        json.dump(perfile, w, ensure_ascii=False, indent=2)

    return {
        "file": fp,
        "ok": shape["ok"],
        "missing": shape["missing"],
        "empty": shape["empty"],
        "written": outfp,
    }


def main():
    p = argparse.ArgumentParser(prog="ocers-ensemble")
    p.add_argument("--in", dest="indir", required=True, help="Input directory of *.json")
    p.add_argument("--out", dest="outdir", required=True, help="Output directory")
    args = p.parse_args()

    indir = os.path.abspath(args.indir)
    outdir = os.path.abspath(args.outdir)

    if not os.path.isdir(indir):
        print(json.dumps({"status": "error", "error": f"not_a_dir: {indir}"}))
        sys.exit(2)

    files = sorted(glob(os.path.join(indir, "*.json")))
    results = []
    for fp in files:
        results.append(_process_file(fp, outdir))

    valid = sum(1 for r in results if r.get("ok"))
    invalid = sum(1 for r in results if r.get("ok") is False)
    report = {
        "status": "ok",
        "in_dir": indir,
        "out_dir": outdir,
        "total_files": len(files),
        "valid": valid,
        "invalid": invalid,
        "results": results,
        "out": "report.json",
    }

    os.makedirs(outdir, exist_ok=True)
    report_path = os.path.join(outdir, "report.json")
    with open(report_path, "w", encoding="utf-8") as w:
        json.dump(report, w, ensure_ascii=False, indent=2)

    print(json.dumps({"status": "ok", "out": "ocers_out/report.json"}))
    sys.exit(0 if invalid == 0 else 1)


if __name__ == "__main__":
    main()
