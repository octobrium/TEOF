#!/usr/bin/env python3
"""
TEOF Eval CLI (minimal)
- validate: run OCERS validator on a file
- score:    run OCERS scorer on a file
- from-url: fetch a URL, extract text, produce a starter OCERS (or call your generator)
"""
import argparse, sys, os, json, subprocess, datetime, re
from typing import Optional

# ---------- utils ----------
def utc_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def repo_root() -> str:
    # Resolve repo root from this file location
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))

def run(cmd, **kw):
    p = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def sha256_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()

# ---------- validator / scorer wrappers ----------
def validate(input_path: str, commit: str) -> int:
    root = repo_root()
    validator = os.path.join(root, "extensions", "validator", "teof_validator.py")
    runmeta = os.path.join(root, "extensions", "validator", "sample_outputs", "runmeta.json")
    if not os.path.isfile(runmeta):
        os.makedirs(os.path.dirname(runmeta), exist_ok=True)
        with open(runmeta, "w") as f:
            json.dump({"model": "local", "runner_digest": "cli", "temp": "0"}, f)
    cmd = f'python3 "{validator}" --input "{input_path}" --runmeta "{runmeta}" --commit "{commit}"'
    code, out, err = run(cmd)
    print(out)
    if err:
        print(err, file=sys.stderr)
    return code

def score(input_path: str, commit: str) -> int:
    root = repo_root()
    scorer = os.path.join(root, "extensions", "scoring", "teof_score.py")
    cmd = f'python3 "{scorer}" --input "{input_path}" --commit "{commit}"'
    code, out, err = run(cmd)
    print(out)
    if err:
        print(err, file=sys.stderr)
    return code

# ---------- robust URL → text extractor ----------
def extract_text_from_url(url: str) -> str:
    """
    Robust download & extraction:
      1) trafilatura.fetch_url + trafilatura.extract
      2) requests.get with browser-like headers + readability-lxml
    Returns plain text (stripped). Empty string on failure.
    """
    try:
        import trafilatura
    except Exception:
        trafilatura = None  # optional

    try:
        if trafilatura is not None:
            downloaded = trafilatura.fetch_url(url, no_ssl=True)
            if downloaded:
                extracted = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=False,
                    include_formatting=False,
                    favor_recall=True,
                )
                if extracted and extracted.strip():
                    return extracted.strip()
    except Exception as e:
        print(f"[extract] trafilatura fallback due to: {e}", file=sys.stderr)

    # Fallback: requests + readability with browser headers
    try:
        import requests
        from bs4 import BeautifulSoup
        from readability import Document
    except Exception:
        return ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()

    doc = Document(resp.text)
    html_main = doc.summary() or resp.text
    text = BeautifulSoup(html_main, "lxml").get_text("\n")

    # Collapse multiple blank lines
    lines = [ln.strip() for ln in text.splitlines()]
    keep = []
    for ln in lines:
        if not ln:
            if keep and keep[-1] != "":
                keep.append("")
        else:
            keep.append(ln)
    return "\n".join(keep).strip()

# ---------- OCERS helpers ----------
def starter_ocers_from_text(text: str) -> dict:
    """
    Heuristic starter. Guarantees non-empty C by taking the next 1–2 paragraphs,
    or falling back to the first paragraph if the page is very short.
    """
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    O = paras[0][:400] if paras else ""
    if len(paras) > 1:
        C = "\n\n".join(paras[1:3])[:800]
    else:
        # backstop: reuse part of the first paragraph to avoid empty C
        C = (paras[0][:400] if paras else "")

    # Leave E/R/S empty unless generator fills; validator only requires C not empty
    E = ""
    R = ""
    S = ""
    return {"O": O, "C": C, "E": E, "R": R, "S": S}

def from_url(url: str, output_path: str, generator_cmd: Optional[str], commit: str) -> int:
    text = extract_text_from_url(url)
    if not text:
        print("ERROR: could not extract text from URL (install deps?).", file=sys.stderr)
        print("Tip: pip install trafilatura requests beautifulsoup4 readability-lxml lxml", file=sys.stderr)
        return 2

    ocers = starter_ocers_from_text(text)

    # Optional generator hook: stdin=text → stdout=OCERS JSON
    if generator_cmd:
        try:
            p = subprocess.run(
                generator_cmd,
                input=text,
                text=True,
                shell=True,
                capture_output=True,
                timeout=120,
            )
            if p.returncode != 0:
                print("Generator command failed:", p.stderr, file=sys.stderr)
            else:
                try:
                    gen = json.loads(p.stdout)
                    if isinstance(gen, dict):
                        # Only overwrite with non-empty values
                        for k in ["O", "C", "E", "R", "S"]:
                            v = (gen.get(k, "") or "").strip()
                            if v:
                                ocers[k] = v
                except Exception as e:
                    print("Generator did not return valid JSON:", e, file=sys.stderr)
        except Exception as e:
            print("Generator execution error:", e, file=sys.stderr)

    # FINAL SAFETY: if C still empty, back-fill from source text
    if not ocers.get("C", "").strip():
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        ocers["C"] = "\n\n".join(paras[1:3])[:800] if len(paras) > 1 else (paras[0][:400] if paras else "Context unavailable.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(ocers, f, indent=2)

    print(f"Wrote OCERS to {output_path}")
    vcode = validate(output_path, commit)
    scode = score(output_path, commit)
    return 0 if (vcode == 0 and scode == 0) else 1

# ---------- CLI ----------
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
    ap_url.add_argument(
        "--generator-cmd",
        default=None,
        help="Optional shell cmd that reads page text on stdin and prints OCERS JSON to stdout."
    )
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
