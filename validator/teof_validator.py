#!/usr/bin/env python3
import sys, json, re, hashlib, time, argparse, pathlib

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()

def parse_text_to_ocers(txt: str):
    # Accept either JSON or headinged text with O/C/E/R/S labels.
    try:
        obj = json.loads(txt)
        if all(k in obj for k in ["O","C","E","R","S"]):
            return {k: str(obj.get(k,"")).strip() for k in ["O","C","E","R","S"]}, True
    except Exception:
        pass
    # Heading parse (e.g., "O — Observation:" etc.), tolerant to punctuation.
    patt = r'(?s)\bO\b.*?:\s*(.*?)\n\s*C\b.*?:\s*(.*?)\n\s*E\b.*?:\s*(.*?)\n\s*R\b.*?:\s*(.*?)\n\s*S\b.*?:\s*(.*)'
    m = re.search(patt, txt, flags=re.IGNORECASE)
    if not m: return None, False
    keys = ["O","C","E","R","S"]
    vals = [v.strip() for v in m.groups()]
    return dict(zip(keys, vals)), False

def check_reversible_steps(step_text: str):
    # Minimal v0: require the word 'reversible' or a clear rollback verb.
    return bool(re.search(r'\brevers(ible|e|al)\b|\brollback\b|\bbackout\b|\bdry[- ]?run\b', step_text, re.I))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to model output (txt or json)")
    ap.add_argument("--runmeta", required=True, help="JSON with run metadata (model, runner_digest, temp)")
    ap.add_argument("--commit", required=True, help="Repo commit SHA (or artifact id)")
    args = ap.parse_args()

    out_bytes = pathlib.Path(args.input).read_bytes()
    out_text  = out_bytes.decode("utf-8", errors="ignore")
    meta = json.loads(pathlib.Path(args.runmeta).read_text())

    ocers, is_json = parse_text_to_ocers(out_text)
    reasons = []
    passed = True

    if not ocers:
        passed = False
        reasons.append("Missing or unparsable O–C–E–R–S")

    if ocers:
        # Non-empty check
        for k in ["O","C","E","R","S"]:
            if not ocers[k].strip():
                passed = False; reasons.append(f"{k} empty")

        # Reversibility check (v0 minimal)
        if not check_reversible_steps(ocers["S"]):
            passed = False; reasons.append("Steps lack reversibility signal (e.g., rollback/dry-run)")

    # Determinism hint: ensure temp=0 declared
    if str(meta.get("temp","")).strip() not in ["0","0.0", "zero"]:
        reasons.append("Warning: temp is not 0 per runmeta")

    # Receipt
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt = (
        f"teof-repro | commit {args.commit} | runner {meta.get('runner_digest','unknown')} "
        f"| model {meta.get('model','unknown')} | temp {meta.get('temp','unknown')} "
        f"| out_sha256 {sha256_bytes(out_bytes)} | ocers_json {is_json} | verdict {'PASS' if passed else 'FAIL'} "
        f"| utc {ts}"
    )
    print(receipt)
    if reasons:
        print("reasons:", "; ".join(reasons))
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
