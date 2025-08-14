#!/usr/bin/env python3
"""
TEOF Eval CLI (minimal)
- validate: run OCERS validator on a file
- score:    run OCERS scorer on a file
- from-url: fetch a URL, extract text, produce a starter OCERS (or call your generator)
"""
import argparse, sys, os, json, subprocess, textwrap, tempfile, hashlib, datetime

def utc_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"

# --- helpers ---
def repo_root():
    # Resolve repo root from this file location
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))

def run(cmd, **kw):
    p = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def sha256_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()

def validate(input_path: str, commit: str):
    root = repo_root()
    validator = os.path.join(root, "extensions", "validator", "teof_validator.py")
    runmeta = os.path.join(root, "extensions", "validator", "sample_outputs", "runmeta.json")
    if not os.path.isfile(runmeta):
        # create a minimal runmeta if missing
        os.makedirs(os.path.dirname(runmeta), exist_ok=True)
        with open(runmeta, "w") as f:
            json.dump({"model": "local", "runner_digest": "cli", "temp": "0"}, f)

    cmd = f'python3 "{validator}" --input "{input_path}" --runmeta "{runmeta}" --commit "{commit}"'
    code, out, err = run(cmd)
    print(out)
    if err:
        print(err, file=sys.stderr)
    return code

def score(input_path: str, commit: str):
    root = repo_root()
    scorer = os.path.join(root, "extensions", "scoring", "teof_score.py")
    cmd = f'python3 "{scorer}" --input "{input_path}" --commit "{commit}"'
    code, out, err = run(cmd)
    print(out)
    if err:
        print(err, file=sys.stderr)
    return code

def extract_text_from_url(url: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception:
        return ""
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # remove script/style
    for tag in soup(["script","style","noscript"]): tag.decompose()
    # prefer article-ish content if present
    main = soup.find("article") or soup.find("main") or soup.body
    text = main.get_text(separator="\n", strip=True) if main else soup.get_text("\n", strip=True)
    # compress blank lines
    lines = [ln.strip() for ln in text.splitlines()]
    keep = []
    for ln in lines:
        if not ln: 
            if keep and keep[-1] != "": keep.append("")
        else:
            keep.append(ln)
    return "\n".join(keep).strip()

def starter_ocers_from_text(text: str) -> dict:
    # Heuristic starter (user can edit, or use generator hook)
    # Take first few non-empty paragraphs
    paras = [p for p in (text.split("\n\n")) if p.strip()]
    O = paras[0][:400] if paras else ""
    C = "\n".join(paras[1:3])[:800] if len(paras) > 1 else ""
    E = ""   # leave empty unless generator fills
    R = ""   # leave empty unless generator fills
    S = ""   # leave empty unless generator fills
    return {"O":O, "C":C, "E":E, "R":R, "S":S}

def from_url(url: str, output_path: str, generator_cmd: str|None, commit: str):
    text = extract_text_from_url(url)
    if not text:
        print("ERROR: requests/bs4 not installed or could not extract text from URL.", file=sys.stderr)
        print("Tip: pip install requests beautifulsoup4", file=sys.stderr)
        return 2

    ocers = starter_ocers_from_text(text)

    if generator_cmd:
        # Optional: pipe extracted text to user's generator command; expect OCERS JSON on stdout
        # The command should read from stdin and emit {"O":...,"C":...,"E":...,"R":...,"S":...}
        try:
            p = subprocess.run(generator_cmd, input=text, text=True, shell=True, capture_output=True, timeout=90)
            if p.returncode != 0:
                print("Generator command failed:", p.stderr, file=sys.stderr)
            else:
                try:
                    gen = json.loads(p.stdout)
                    if isinstance(gen, dict):
                        ocers.update({k:str(gen.get(k,"")).strip() for k in ["O","C","E","R","S"]})
                except Exception as e:
                    print("Generator did not return valid JSON:", e, file=sys.stderr)
        except Exception as e:
            print("Generator execution error:", e, file=sys.stderr)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(ocers, f, indent=2)

    print(f"Wrote OCERS to {output_path}")
    # Immediate validate + score to feel usefulness
    vcode = validate(output_path, commit)
    scode = score(output_path, commit)
    return 0 if (vcode == 0 and scode == 0) else 1

def main():
    ap = argparse.ArgumentParser(description="TEOF Eval CLI (validate, score, from-url)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_val = sub.add_parser("validate")
    ap_val.add_argument("--input", required=True)
    ap_val.add_argument("--commit", default="local")

    ap_sco = sub.add_parser("score")
    ap_sco.add_argument("--input", required=True)
    ap_sco.add_argument("--commit", default="local")

    ap_url = sub.add_parser("from-url")
    ap_url.add_argument("--url", required=True)
    ap_url.add_argument("--output", default="extensions/scoring/out/ocers_from_url.json")
    ap_url.add_argument("--generator-cmd", default=None,
                        help="Optional shell cmd that reads page text on stdin and prints OCERS JSON to stdout.")
    ap_url.add_argument("--commit", default="local")

    args = ap.parse_args()
    if args.cmd == "validate":
        sys.exit(validate(args.input, args.commit))
    if args.cmd == "score":
        sys.exit(score(args.input, args.commit))
    if args.cmd == "from-url":
        sys.exit(from_url(args.url, args.output, args.generator_cmd, args.commit))

if __name__ == "__main__":
    main()
