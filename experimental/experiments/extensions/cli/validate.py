#!/usr/bin/env python3
import argparse, pathlib
from extensions.validator import teof_ocers_min as val

def main():
    p = argparse.ArgumentParser(description="TEOF OCERS validate a single text file.")
    p.add_argument("input", help="Path to input .txt")
    p.add_argument("outdir", help="Directory for outputs")
    args = p.parse_args()

    inpath = pathlib.Path(args.input).resolve()
    outdir = pathlib.Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    raw = val.read_text(str(inpath))
    t = val.norm_text(raw)
    O = val.score_observation(t); C = val.score_coherence(t)
    E = val.score_ethics(t); R = val.score_repro(t); S = val.score_selfrepair(t)
    total = O+C+E+R+S
    verdict = "PASS" if total >= 18 and min(O,C,E,R,S) >= 3 else "NEEDS WORK"

    import json, hashlib, datetime
    out_json = {
        "stamp": datetime.datetime.utcnow().isoformat()+"Z",
        "input_file": inpath.name,
        "hash_sha256": hashlib.sha256(raw.encode("utf-8","ignore")).hexdigest(),
        "ocers": {"O":O,"C":C,"E":E,"R":R,"S":S,"total":total,"verdict":verdict},
        "notes": {
            "O": val.justify("O",O),
            "C": val.justify("C",C),
            "E": val.justify("E",E),
            "R": val.justify("R",R),
            "S": val.justify("S",S),
        }
    }
    base = inpath.stem
    with open(outdir/f"{base}.json","w",encoding="utf-8") as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)
    print(f"[OCERS] {base}: total={total}/25 {verdict} (O={O} C={C} E={E} R={R} S={S})")

if __name__ == "__main__":
    main()
