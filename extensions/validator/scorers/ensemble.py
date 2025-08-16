#!/usr/bin/env python3
import json, pathlib, importlib

def load_text(path):
    return pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")

def run_heuristic(text):
    mod = importlib.import_module("extensions.validator.teof_ocers_min")
    t = mod.norm_text(text)
    O = mod.score_observation(t); C = mod.score_coherence(t)
    E = mod.score_ethics(t); R = mod.score_repro(t); S = mod.score_selfrepair(t)
    return {"O":O,"C":C,"E":E,"R":R,"S":S,"name":"H"}

RUNNERS = {"H": run_heuristic}

def ensemble(scores, weights=None):
    if weights is None:
        weights = {s["name"]: 1.0 for s in scores}
    out = {}
    for k in ["O","C","E","R","S"]:
        num = sum(s[k] * weights.get(s["name"], 1.0) for s in scores)
        den = sum(weights.get(s["name"], 1.0) for s in scores)
        out[k] = round(num / den, 2)
    out["total"] = round(sum(out[k] for k in ["O","C","E","R","S"]), 2)
    return out

def score_file(inp, which=("H",), weights=None):
    text = load_text(inp)
    parts = []
    for tag in which:
        parts.append(RUNNERS[tag](text))
    agg = ensemble(parts, weights)
    return {"by_scorer": parts, "ensemble": agg}
