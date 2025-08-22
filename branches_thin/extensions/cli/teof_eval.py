#!/usr/bin/env python3
"""
TEOF Eval CLI (minimal, hardened)
- validate: run OCERS validator on a file
- score:    run OCERS scorer on a file
- from-url: fetch a URL, extract text, produce a starter OCERS (or call your generator)
- batch:    process many URLs from a text file (one per line)
"""
import argparse, sys, os, json, subprocess, datetime, re, hashlib, urllib.parse
from typing import Optional, Tuple

# ---------- utils ----------
def utc_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def repo_root() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))

def run(cmd, **kw):
    p = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def safe_name_from_url(url: str) -> str:
    u = urllib.parse.urlparse(url)
    base = (u.netloc + u.path).strip("/")
    base = re.sub(r"[^A-Za-z0-9._/-]+", "-", base)
    base = base.replace("/", "-")
    base = re.sub(r"-{2,}", "-", base).strip("-")
    return base or "item"

# ---------- validator / scorer wrappers ----------
def validate(input_path: str, commit: str) -> int:
    root = repo_root()
    validator = os.path.join(root, "extensions", "validator", "teof_validator.py")
    runmeta = os.path.join(root, "extensions", "validator", "sample_outputs", "runmeta.json")
    if not os.path.isfile(runmeta):
        os.makedirs(os.path.dirname(runmeta), exist_ok=True)
        with open(runmeta, "w") as f:
            json.dump({"model": "local", "runner_digest": "cli", "temp": "0"}, f)
    code, out, err = run(f'python3 "{validator}" --input "{input_path}" --runmeta "{runmeta}" --commit "{commit}"')
    print(out)
    if err:
        print(err, file=sys.stderr)
    return code

def score(input_path: str, commit: str) -> int:
    root = repo_root()
    scorer = os.path.join(root, "extensions", "scoring", "teof_score.py")
    code, out, err = run(f'python3 "{scorer}" --input "{input_path}" --commit "{commit}"')
    print(out)
    if err:
        print(err, file=sys.stderr)
    return code

# ---------- robust URL → text extractor ----------
def extract_text_with_method(url: str) -> Tuple[str, str]:
    """
    Robust download & extraction:
      1) trafilatura.fetch_url + trafilatura.extract
      2) requests.get with browser-like headers + readability-lxml
    Returns (plain_text, method_tag). Empty text on failure.
    """
    method = "none"
    # Try trafilatura first
    try:
        import trafilatura
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
                return extracted.strip(), "trafilatura"
    except Exception as e:
        print(f"[extract] trafilatura fallback due to: {e}", file=sys.stderr)

    # Fallback: requests + readability
    try:
        import requests
        from bs4 import BeautifulSoup
        from readability import Document
    except Exception:
        return "", method

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
    import requests as _rq
    resp = _rq.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    try:
        doc = Document(resp.text)
        html_main = doc.summary() or resp.text
    except Exception:
        html_main = resp.text
    from bs4 import BeautifulSoup as _BS
    text = _BS(html_main, "lxml").get_text("\n")
    # De-blank
    lines = [ln.strip() for ln in text.splitlines()]
    keep = []
    for ln in lines:
        if not ln:
            if keep and keep[-1] != "":
                keep.append("")
        else:
            keep.append(ln)
    text = "\n".join(keep).strip()
    return text, "readability"

def extract_text_from_url(url: str) -> str:
    # backwards compat wrapper
    txt, _ = extract_text_with_method(url)
    return txt

# ---------- OCERS helpers ----------
def starter_ocers_from_text(text: str) -> dict:
    """
    Heuristic starter:
    - O: first paragraph (≤400 chars)
    - C: next 1–2 paragraphs (≤800 chars)
      Fallbacks if empty: take first 800 chars of remainder; then O slice.
    - E/R/S: empty (optionally filled by generator)
    """
    # normalize & split paras
    norm = re.sub(r'\r\n?', '\n', text)
    paras = [p.strip() for p in re.split(r'\n\s*\n+', norm) if p.strip()]

    O = paras[0][:400] if paras else ""

    C = ""
    if len(paras) > 1:
        C = "\n".join(paras[1:3])[:800].strip()

    if not C:
        remainder = norm[len(paras[0]):].strip() if paras else norm
        C = remainder[:800].strip()

    if not C and O:
        C = O[:300].strip()

    E = ""
    R = ""
    S = ""
    return {"O": O, "C": C, "E": E, "R": R, "S": S}

def enrich_ocers_fields(ocers: dict, text: str) -> None:
    """Light-touch enrichment: only fill Reasoning if empty."""
    if not ocers.get("R"):
        sents = re.split(r"(?<=[.!?])\s+", text)
        because = [s for s in sents if re.search(r"\b(because|due to|driven by|as a result)\b", s, re.I)]
        nums = re.findall(r"\b\d[\d,\.%]*\b", text)
        bullets = []
        if because[:2]:
            bullets.extend([f"- {s.strip()}" for s in because[:2]])
        if nums[:5]:
            bullets.append("- Key figures: " + ", ".join(nums[:5]))
        if not bullets:
            bullets = [
                "- Drivers: summarize the main causes or forces at play.",
                "- Risks: what could fail; where are the uncertainties?",
                "- Assumptions: what must be true for the claims to hold."
            ]
        ocers["R"] = "Reasoning:\n" + "\n".join(bullets)

# ---------- core ops ----------
def from_url(url: str, output_path: str, generator_cmd: Optional[str], commit: str) -> int:
    text, method = extract_text_with_method(url)
    if not text:
        print("ERROR: could not extract text from URL.", file=sys.stderr)
        print("Tip: pip install trafilatura requests beautifulsoup4 readability-lxml lxml", file=sys.stderr)
        return 2

    if len(text) < 300:
        print(f"Warning: very short extraction ({len(text)} chars). Results may be weak.", file=sys.stderr)

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
                        ocers.update({k: str(gen.get(k, "")).strip() for k in ["O", "C", "E", "R", "S"]})
                except Exception as e:
                    print("Generator did not return valid JSON:", e, file=sys.stderr)
        except Exception as e:
            print("Generator execution error:", e, file=sys.stderr)

    # Light enrichment (only if R still empty)
    enrich_ocers_fields(ocers, text)

    # Warn if key fields are empty before validate/score
    for k in ("O", "C", "E"):
        if not ocers.get(k):
            print(f"Warning: field {k} is empty before validate/score.", file=sys.stderr)

    # Write OCERS
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(ocers, f, indent=2)

    # --- provenance: raw text + meta next to the OCERS file ---
    raw_txt_path = output_path + ".source.txt"
    meta_path    = output_path + ".meta.json"
    try:
        with open(raw_txt_path, "w") as f:
            f.write(text)
    except Exception as e:
        print(f"Warning: could not write raw text: {e}", file=sys.stderr)

    try:
        ocers_sha = sha256_bytes(json.dumps(ocers, sort_keys=True).encode("utf-8"))
        meta = {
            "url": url,
            "utc": utc_iso(),
            "commit": commit,
            "extractor": method,
            "text_sha256": sha256_bytes(text.encode("utf-8")),
            "ocers_sha256": ocers_sha,
            "raw_text_path": os.path.basename(raw_txt_path),
            "tool": "teof_eval.py",
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        print(f"Warning: could not write meta: {e}", file=sys.stderr)

    print(f"Wrote OCERS to {output_path}")
    vcode = validate(output_path, commit)
    scode = score(output_path, commit)
    return 0 if (vcode == 0 and scode == 0) else 1

def batch(file_path: str, out_dir: str, generator_cmd: Optional[str], commit: str) -> int:
    os.makedirs(out_dir, exist_ok=True)
    summary_path = os.path.join(out_dir, f"summary_{utc_iso().replace(':','')}.csv")
    ok_all = True
    with open(file_path, "r") as f, open(summary_path, "w") as s:
        s.write("url,out_path,validate_rc,score_rc\n")
        for idx, line in enumerate(f, 1):
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            base = safe_name_from_url(url)
            out = os.path.join(out_dir, f"{base}_{idx}.json")
            rc = from_url(url, out, generator_cmd, commit)
            # We can’t easily split validate vs score rc here because from_url calls both;
            # record rc twice for a simple pass/fail signal.
            s.write(f"{json.dumps(url)},{json.dumps(out)},{rc},{rc}\n")
            ok_all = ok_all and (rc == 0)
    print(f"Batch summary → {summary_path}")
    return 0 if ok_all else 1

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="TEOF Eval CLI (validate, score, from-url, batch)")
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

    ap_batch = sub.add_parser("batch")
    ap_batch.add_argument("--file", required=True, help="Text file with one URL per line")
    ap_batch.add_argument("--out-dir", default="extensions/scoring/out/batch")
    ap_batch.add_argument("--generator-cmd", default=None)
    ap_batch.add_argument("--commit", default="local")

    args = ap.parse_args()
    if args.cmd == "validate":
        sys.exit(validate(args.input, args.commit))
    if args.cmd == "score":
        sys.exit(score(args.input, args.commit))
    if args.cmd == "from-url":
        sys.exit(from_url(args.url, args.output, args.generator_cmd, args.commit))
    if args.cmd == "batch":
        sys.exit(batch(args.file, args.out_dir, args.generator_cmd, args.commit))

if __name__ == "__main__":
    main()
