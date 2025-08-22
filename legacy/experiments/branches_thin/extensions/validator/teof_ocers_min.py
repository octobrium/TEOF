#!/usr/bin/env python3
"""
TEOF OCERS Minimal Heuristic Validator (v0.4)
- Tuned for journalism: attribution ('said', 'according to'), multiple actors, numbers/dates
- Keeps unicode normalization + lowercasing
"""

import sys, json, re, hashlib, datetime, os, pathlib, unicodedata

def read_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def norm_text(t: str) -> str:
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"\s+", " ", t)
    return t.lower().strip()

def count_patterns(t: str, patterns):
    return sum(len(re.findall(p, t, re.I)) for p in patterns)

# ------------ Scorers ------------

def score_observation(t: str) -> int:
    obs      = count_patterns(t, [r"\bobserv", r"\bmeasure", r"\bdata\b", r"\bevidence\b"])
    humility = count_patterns(t, [r"\buncertain", r"\bassumption", r"\bmight\b", r"\bcould\b", r"\bwe recognize\b"])
    attrib   = count_patterns(t, [r"\baccording to\b", r"\bsaid\b", r"\breported\b", r"\bcited\b", r"\banalysts?\b", r"\bpolicymakers?\b"])
    quotes   = t.count('"') + t.count('“') + t.count('”')
    s = 1 + min(2, obs) + min(2, humility)
    # Journalism attribution/quotes count as observation signals
    if attrib > 0: s += 1
    if quotes >= 2: s += 1
    return max(1, min(5, s))

def score_coherence(t: str) -> int:
    logic = count_patterns(t, [r"\btherefore\b", r"\bthus\b", r"\bhence\b", r"\bconclude", r"\bbecause\b", r"\bpremise\b"])
    contradictions = count_patterns(t, [r"\bcontradict", r"\binconsistent", r"\bparadox"])
    s = 2 + min(2, logic) - min(2, contradictions)
    # Neutral news often lists facts without formal logic; don't go below 3 if well-attributed
    if count_patterns(t, [r"\bsaid\b", r"\baccording to\b"]) >= 2:
        s = max(s, 3)
    return max(1, min(5, s))

def score_ethics(t: str) -> int:
    pro = count_patterns(t, [r"\btransparen", r"\bethic", r"\bresponsib", r"\baccountab", r"\baudit", r"\bpublic\b", r"\bopen(-|\s)?source"])
    con = count_patterns(t, [r"\bmanipulat", r"\bexploit", r"\bdeceiv", r"\bobfuscat", r"\bthey don'?t want you to know", r"\bdon'?t trust (government|media)"])
    s = 2 + min(3, pro) - min(2, con)
    # Straight news w/ neutral verbs gets a floor of 3 unless manipulative language appears
    if con == 0 and count_patterns(t, [r"\bsaid\b", r"\breported\b", r"\baccording to\b"]) > 0:
        s = max(s, 3)
    return max(1, min(5, s))

def score_repro(t: str) -> int:
    methods  = count_patterns(t, [r"\bmethod", r"\bprocedure", r"\breplicat", r"\bexperiment", r"\bprotocol", r"\bchecklist"])
    cites    = count_patterns(t, [r"\bsource", r"\bcite", r"\breference", r"\bappendix", r"\bdoi\b", r"http(s)?://"])
    numbers  = len(re.findall(r"\b\d+(\.\d+)?%?\b", t))
    code_data= count_patterns(t, [r"\bcode\b", r"\breleased?\b", r"\bgithub\b", r"\bdataset"])
    attrib   = count_patterns(t, [r"\bsaid\b", r"\baccording to\b", r"\banalysts?\b", r"\bpolicymakers?\b"])
    multi_attrib = attrib >= 2
    s = 1
    if methods > 0:  s += 2
    if cites   > 0:  s += 2
    if numbers > 1:  s += 1
    if code_data> 0: s += 1
    if multi_attrib: s += 1  # multiple independent sources ~ reproducibility signal
    # Floor for factual news with at least one number + one attribution
    if numbers > 0 and attrib > 0:
        s = max(s, 3)
    return max(1, min(5, s))

def score_selfrepair(t: str) -> int:
    repair = count_patterns(t, [r"\btest", r"\bverify", r"\baudit", r"\bmonitor", r"\bincident reporting", r"\bpostmortem", r"\bfallback", r"\brollback", r"\bpause\b", r"\boversight", r"\bindependent review", r"\bred team", r"\bupdate"])
    s = 1 + min(4, repair)
    return max(1, min(5, s))

def justify(name, s):
    tips = {
        'O': "Use evidence/uncertainty or attributed reporting.",
        'C': "Keep claims consistent; connect facts to conclusions.",
        'E': "Avoid manipulative framing; prefer transparency.",
        'R': "Provide sources/figures; multiple attributions help.",
        'S': "Include audits/monitoring/rollback or incident reporting."
    }
    return f"{name}={s}/5 — {tips[name]}"

def main():
    if len(sys.argv) < 3:
        print("Usage: teof_ocers_min.py <input.txt> <outdir>")
        sys.exit(2)
    inpath = pathlib.Path(sys.argv[1]).resolve()
    outdir = pathlib.Path(sys.argv[2]).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    raw  = read_text(str(inpath))
    text = norm_text(raw)

    O = score_observation(text)
    C = score_coherence(text)
    E = score_ethics(text)
    R = score_repro(text)
    S = score_selfrepair(text)
    total = O + C + E + R + S
    verdict = "PASS" if total >= 18 and min(O, C, E, R, S) >= 3 else "NEEDS WORK"

    src_hash = hashlib.sha256(raw.encode("utf-8","ignore")).hexdigest()
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

    print(f"[OCERS] {base}: total={total}/25 verdict={verdict} (O={O} C={C} E={E} R={R} S={S})")

if __name__ == "__main__":
    main()
