#!/usr/bin/env python3
import sys, json, re, hashlib, datetime, os, pathlib

def read_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def score_observation(t):
    hits = bool(re.search(r"\b(observation|observe|observer|perception|experience|measurement)\b", t, re.I))
    anti_dogma = bool(re.search(r"\b(i might be wrong|unknown|uncertain|assumption)\b", t, re.I))
    if hits and anti_dogma: return 5
    if hits: return 4
    if anti_dogma: return 3
    return 1

def score_coherence(t):
    contradictions = len(re.findall(r"\b(contradict|inconsistent)\b", t, re.I))
    structure = bool(re.search(r"\b(therefore|thus|hence|premise|assume|conclude|implies)\b", t, re.I))
    s = 3 + (1 if structure else 0) - min(2, contradictions)
    return max(1, min(5, s))

def score_ethics(t):
    pro = len(re.findall(r"\b(clarity|transparen|improv|coheren|truth)\w*\b", t, re.I))
    con = len(re.findall(r"\b(manipulat|deceiv|obfuscat)\w*\b", t, re.I))
    s = 2 + min(3, pro) - min(2, con)
    return max(1, min(5, s))

def score_repro(t):
    steps = len(re.findall(r"\b(step|procedure|method|checklist|repeat|replicat|code|algorithm)\w*\b", t, re.I))
    cites = len(re.findall(r"\b(source|cite|reference|appendix)\b", t, re.I))
    s = 1 + min(2, steps) + min(2, cites)
    return max(1, min(5, s))

def score_selfrepair(t):
    repair = len(re.findall(r"\b(test|verify|audit|monitor|fallback|rollback|error|bug|fix|update)\b", t, re.I))
    s = 1 + min(4, repair)
    return max(1, min(5, s))

def justify(name, s):
    tips = {
        'O': "State observation/uncertainty explicitly; avoid dogma.",
        'C': "Show premises → inference → conclusion; remove contradictions.",
        'E': "Add commitments to transparency, clarity, and systemic benefit.",
        'R': "Include steps or checks another can repeat.",
        'S': "Add tests/audits and what happens if a check fails."
    }
    return f"{name}={s}/5 — {tips[name]}"

def render_report_md(base, ocers, notes, src_hash):
    lines = []
    lines.append(f"# OCERS Evaluation: {base}")
    lines.append("")
    lines.append(f"**Scores:** O={ocers['O']}, C={ocers['C']}, E={ocers['E']}, R={ocers['R']}, S={ocers['S']} → Total={ocers['total']}/25")
    lines.append(f"**Verdict:** {ocers['verdict']}")
    lines.append("")
    lines.append("**Notes:**")
    for k in ["O","C","E","R","S"]:
        lines.append(f"- {notes[k]}")
    lines.append("")
    lines.append(f"_Source SHA-256_: `{src_hash}`")
    lines.append("")
    return "\n".join(lines)

def main():
    if len(sys.argv) < 3:
        print("Usage: teof_ocers_min.py <input.txt> <outdir>")
        sys.exit(2)
    inpath = pathlib.Path(sys.argv[1]).resolve()
    outdir = pathlib.Path(sys.argv[2]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    text = read_text(str(inpath))
    O = score_observation(text)
    C = score_coherence(text)
    E = score_ethics(text)
    R = score_repro(text)
    S = score_selfrepair(text)
    total = O + C + E + R + S
    verdict = "PASS" if total >= 18 and min(O,C,E,R,S) >= 3 else "NEEDS-WORK"

    src_hash = hashlib.sha256(text.encode("utf-8","ignore")).hexdigest()
    stamp = datetime.datetime.utcnow().isoformat()+"Z"
    base = inpath.stem

    out_json = {
        "stamp": stamp,
        "input_file": inpath.name,
        "hash_sha256": src_hash,
        "ocers": {"O":O,"C":C,"E":E,"R":R,"S":S,"total":total,"verdict":verdict},
        "notes": {
            "O": justify("O",O),
            "C": justify("C",C),
            "E": justify("E",E),
            "R": justify("R",R),
            "S": justify("S",S),
        }
    }
    with open(outdir/f"{base}.json","w",encoding="utf-8") as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)

    report_md = render_report_md(base, out_json["ocers"], out_json["notes"], src_hash)
    with open(outdir/f"{base}.report.md","w",encoding="utf-8") as f:
        f.write(report_md)

    print(f"[OCERS] {base}: total={total}/25 verdict={verdict}  (O={O} C={C} E={E} R={R} S={S})")
    print(f"→ wrote {outdir}/{base}.json and {outdir}/{base}.report.md")

if __name__ == "__main__":
    main()
