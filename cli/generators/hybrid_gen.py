#!/usr/bin/env python3
import sys, json, re, argparse, subprocess

REQ = ["O","C","E","R","S"]

def heuristic_ocers(text: str) -> dict:
    # Split on blank lines, grab a few early paragraphs
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    O = paras[0][:400] if paras else ""
    C = "\n".join(paras[1:3])[:800] if len(paras) > 1 else ""

    # Evidence heuristics
    nums   = re.findall(r"\b\d[\d,\.%]*\b", text)
    links  = re.findall(r"https?://\S+", text)
    quotes = re.findall(r"[“\"']([^”\"']{12,280})[”\"']", text)

    evid_bits = []
    if nums:   evid_bits.append(f"numbers: {', '.join(nums[:6])}")
    if links:  evid_bits.append("links:\n- " + "\n- ".join(links[:5]))
    if quotes: evid_bits.append("quotes:\n- " + "\n- ".join(quotes[:4]))
    E = "\n".join(evid_bits)[:1200]

    # Minimal R/S placeholders (scorer will nudge you higher)
    R = "Assumptions/biases not fully extracted; verify sources; note missing counterpoints."
    S = "1) Verify key facts from ≥2 sources.\n2) Extract core numbers/dates.\n3) Summarize risks and next steps."

    return {"O": O, "C": C, "E": E, "R": R, "S": S}

def run_llm(llm_cmd: str, text: str) -> dict:
    """
    Call any local/remote LLM via shell command.
    Contract: read plaintext on stdin, print OCERS JSON on stdout.
    Examples you can pass as --llm-cmd (choose one you actually have):
      - "python3 path/to/my_llm_wrapper.py"
      - "ollama run llama3.1"
      - "openai chat.completions.create --model gpt-4o-mini --input-file -"
    """
    p = subprocess.run(llm_cmd, input=text, text=True, shell=True,
                       capture_output=True, timeout=120)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "LLM command failed")
    data = json.loads(p.stdout)
    if not isinstance(data, dict):
        raise ValueError("Generator output was not a JSON object")
    # Keep only REQ keys as strings
    return {k: str(data.get(k, "")).strip() for k in REQ}

def merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k in REQ:
        v = (override.get(k) or "").strip()
        if v:
            out[k] = v
    return out

def main():
    ap = argparse.ArgumentParser(description="Hybrid OCERS generator (heuristic + optional LLM)")
    ap.add_argument("--llm-cmd", default=None,
                    help="Optional shell command that reads text on stdin and prints OCERS JSON to stdout")
    args = ap.parse_args()

    text = sys.stdin.read()
    base = heuristic_ocers(text)
    try:
        if args.llm_cmd:
            enriched = run_llm(args.llm_cmd, text)
            base = merge(base, enriched)
    except Exception as e:
        # Fail open: keep heuristic, print warning to stderr
        print(f"WARN: LLM enrichment failed: {e}", file=sys.stderr)

    print(json.dumps(base, indent=2))

if __name__ == "__main__":
    main()
