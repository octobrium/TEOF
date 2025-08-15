#!/usr/bin/env python3
"""
URL/File → OCERS → Validate → Score (deterministic, extractor-first)
- Generators:
  * sample (heuristic, local)
  * advanced (calls hybrid_gen.py)
  * remote-ai (calls hybrid_gen.py with --llm-cmd; set via --llm-cmd or $TEOF_LLM_CMD)
"""

from __future__ import annotations
import argparse, json, os, re, subprocess, sys, time, pathlib
from typing import Optional
from extractors import extract as extract_url  # same dir import

REPO = pathlib.Path(__file__).resolve().parents[2]  # repo root (…/TEOF)

OUT_DIR = REPO / "extensions" / "scoring" / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def now_iso() -> str:
    import datetime as dt
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def commit_short() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO).decode().strip()
    except Exception:
        return "local"

# ---------- Generators ----------
def sample_generator(text: str) -> dict:
    # Minimal, deterministic heuristic to fill OCERS.
    paras = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    O = paras[0][:400] if paras else ""
    C = "\n".join(paras[1:3])[:800] if len(paras) > 1 else ""

    nums = re.findall(r"\b\d[\d,.\%]*\b", text)
    links = re.findall(r"https?://\S+", text)
    quotes = re.findall(r"[“\"']([^”\"']{12,280})[”\"']", text)

    E_lines = []
    if nums:   E_lines.append("numbers: " + ", ".join(nums[:8]))
    if links:  E_lines.append("links:\n- " + "\n- ".join(links[:6]))
    if quotes: E_lines.append("quotes:\n- " + "\n- ".join(quotes[:4]))
    E = "\n".join(E_lines)[:1200]

    R = "Assumptions may be present; verify primary sources; identify counterpoints."
    S = "1) Verify key facts via ≥2 sources.\n2) Extract core numbers/dates.\n3) Summarize risks and next steps."

    return {"O": O, "C": C, "E": E, "R": R, "S": S}

def run_hybrid(text: str, llm_cmd: Optional[str]) -> dict:
    gen = REPO / "extensions" / "cli" / "generators" / "hybrid_gen.py"
    if not gen.exists():
        raise RuntimeError("advanced/remote generators require extensions/cli/generators/hybrid_gen.py")
    cmd = ["python3", str(gen)]
    if llm_cmd:
        cmd += ["--llm-cmd", llm_cmd]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(text)
    if p.returncode != 0:
        raise RuntimeError(f"generator failed: {err.strip()[:400]}")
    try:
        return json.loads(out)
    except Exception as e:
        raise RuntimeError(f"generator produced invalid JSON: {e}")

# ---------- IO helpers ----------
def write_json(path: pathlib.Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def read_text_file(path: pathlib.Path) -> str:
    typ = subprocess.check_output(["file", "-b", str(path)]).decode().lower()
    if "text" in typ or path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace")
    # best-effort: use macOS textutil if available
    if shutil.which("textutil"):
        import tempfile, shutil as _sh
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = pathlib.Path(tmp.name)
        try:
            subprocess.check_call(["textutil", "-convert", "txt", "-stdout", str(path)], stdout=open(tmp_path, "wb"))
            return tmp_path.read_text(encoding="utf-8", errors="replace")
        finally:
            try: tmp_path.unlink()
            except Exception: pass
    # fallback
    return path.read_text(encoding="utf-8", errors="replace")

# ---------- Validator / Score ----------
def run_validator(ocers_path: pathlib.Path, commit: str) -> int:
    vpath = REPO / "validator" / "teof_validator.py"
    runmeta = OUT_DIR / "runmeta.json"
    write_json(runmeta, {"model": "local-sample", "runner_digest": "cli", "temp": "0"})
    p = subprocess.run(["python3", str(vpath),
                        "--input", str(ocers_path),
                        "--runmeta", str(runmeta),
                        "--commit", commit])
    return p.returncode

def run_score(ocers_path: pathlib.Path, commit: str) -> int:
    spath = REPO / "extensions" / "scoring" / "teof_score.py"
    p = subprocess.run(["python3", str(spath),
                        "--input", str(ocers_path),
                        "--commit", commit])
    return p.returncode

# ---------- Main pipeline ----------
def main() -> int:
    ap = argparse.ArgumentParser(description="URL/File → OCERS → validate → score")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="URL to fetch")
    src.add_argument("--file", help="Path to local text/doc file")

    ap.add_argument("--generator", choices=["sample","advanced","remote-ai"], default="sample")
    ap.add_argument("--llm-cmd", help="LLM command for remote-ai (or set $TEOF_LLM_CMD)")
    ap.add_argument("--output", help="Explicit output path (.json). If omitted, uses timestamp in extensions/scoring/out/")
    ap.add_argument("--commit", default=commit_short())
    args = ap.parse_args()

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = pathlib.Path(args.output) if args.output else (OUT_DIR / f"ocers_{ts}.json")

    # 1) Get text
    if args.url:
        try:
            ext = extract_url(args.url)
        except Exception as e:
            print(f"ERROR: extraction failed: {e}", file=sys.stderr)
            return 2
        text = ext.text
        meta = {
            "source": "url",
            "url": ext.url,
            "title": ext.title,
            "extractor": ext.extractor,
            "confidence": ext.confidence,
            "text_sha256": ext.sha256,
            "content_sha256": ext.meta.get("content_sha256"),
            "links": ext.links[:16],
        }
    else:
        p = pathlib.Path(args.file).expanduser()
        if not p.exists():
            print("ERROR: file not found", file=sys.stderr); return 2
        text = read_text_file(p)
        meta = {"source": "file", "path": str(p.resolve())}

    if not text.strip():
        print("ERROR: empty text after extraction", file=sys.stderr)
        return 2

    # 2) Generate OCERS
    ocers = None
    try:
        if args.generator == "sample":
            ocers = sample_generator(text)
        else:
            llm_cmd = args.llm_cmd or os.getenv("TEOF_LLM_CMD")
            ocers = run_hybrid(text, llm_cmd if args.generator == "remote-ai" else None)
    except Exception as e:
        print(f"⚠ generator failed ({e}). Falling back to local sample…", file=sys.stderr)
        ocers = sample_generator(text)

    # 3) Write + provenance
    payload = {**ocers, "OpenQuestions": ""}
    write_json(out, payload)
    print(f"Wrote OCERS → {out}")

    # 4) Validate + score
    rc_v = run_validator(out, args.commit)
    rc_s = run_score(out, args.commit)
    return 0 if rc_v == 0 else 1


if __name__ == "__main__":
    import shutil
    sys.exit(main())
