# Doc Verification – Tier 1 Evaluate Prototype
- Agent: codex-tier2
- Timestamp: 2025-11-08T22:53:51Z
- Claims verified:
  1. `python3 -m teof up --eval` → artifacts/systemic_out/20251108T225351Z with brief + score + metadata + 10 ensembles, receipt `_report/usage/onboarding/tier1-evaluation-20251108T225351Z.json`.
  2. `ls artifacts/systemic_out/20251108T225351Z/*.ensemble.json | wc -l` → `10` (matches documentation claim of 10 sample documents/ensembles).
  3. `ls artifacts/systemic_out/20251108T225351Z/metadata.json` → file exists; JSON captures systemic targets/layer metadata per schema.
- Receipts referenced:
  - `_report/usage/onboarding/tier1-evaluation-20251108T225351Z.json`
  - `artifacts/systemic_out/20251108T225351Z/metadata.json`
