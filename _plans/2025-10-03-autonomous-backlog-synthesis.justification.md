# Justification: 2025-10-03-autonomous-backlog-synthesis

- ND-020 backlog synthesis still depends on manual triage; policy lacks rules for fractal advisories and no receipts are written when automation runs.
- `_plans/next-development.todo.json` shows no advisory-derived items even though `_report/fractal/advisories/latest.json` lists 169 gaps.
- `tools/autonomy/backlog_synth.py` only considers health metrics and emits no proof, making unattended runs unverifiable.
