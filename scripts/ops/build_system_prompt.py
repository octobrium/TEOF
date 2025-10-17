#!/usr/bin/env python3
import json, subprocess, yaml, os
from pathlib import Path

root = Path(__file__).resolve().parents[2]
outdir = root / "_report"
outdir.mkdir(parents=True, exist_ok=True)

def read(p): 
    try: return Path(p).read_text(encoding="utf-8")
    except Exception: return ""

def read_json(p):
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception: return None

def read_yaml(p):
    try: return yaml.safe_load(Path(p).read_text(encoding="utf-8"))
    except Exception: return None

sha = subprocess.run(["git","rev-parse","--short","HEAD"], text=True, capture_output=True, check=True).stdout.strip()

charter   = read(root/"governance/CHARTER.md")
policy    = read_json(root/"governance/policy.json") or {}
objectives= read_yaml(root/"governance/objectives.yaml") or {}
anchors   = read_json(root/"governance/anchors.json") or {}
arch      = read(root/"docs/architecture.md")
flow      = read(root/"docs/workflow.md")
promo     = read(root/"docs/promotion-policy.md")

content = []
content.append(f"# TEOF System Prompt (commit {sha})")
content.append("You are an autonomous assistant operating under the TEOF constitution. You MUST obey the policy and constraints below.")
content.append("\n## Constitution (human-readable)\n")
content.append(charter.strip() or "(no CHARTER.md yet)")
content.append("\n## Policy (machine-readable)\n")
content.append(json.dumps(policy, ensure_ascii=False, indent=2))
if objectives:
    content.append("\n## Objectives (weights/hints)\n")
    content.append(yaml.safe_dump(objectives, sort_keys=False))
if anchors:
    content.append("\n## Anchors (provenance hints)\n")
    content.append(json.dumps(anchors, ensure_ascii=False, indent=2))
content.append("\n## Process (reference excerpts)\n")
if arch:  content.append("### docs/architecture.md\n"  + arch[:4000])
if flow:  content.append("\n### docs/workflow.md\n"      + flow[:3000])
if promo: content.append("\n### docs/promotion-policy.md\n" + promo[:3000])
content.append("""
## Required behavior
- Only modify files that match policy.allow_globs; do not rename or delete files.
- Keep total changed lines ≤ policy.diff_limit.
- Include a systemic alignment receipt with model, inputs (hash), and diff hash.
- Label PRs with policy.labels and ensure required checks pass.
- Fail closed on ambiguity; ask for human review via PR comment rather than guessing.
""")

out = "\n".join(content).rstrip() + "\n"
outfile = outdir / f"system_prompt-{sha}.txt"
outfile.write_text(out, encoding="utf-8")
print(f"Wrote {outfile}")
