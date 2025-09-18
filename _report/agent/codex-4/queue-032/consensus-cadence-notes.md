# Consensus Cadence Notes — 2025-09-18T20:05Z
- Daily async sweep: run ledger + dashboard CLI (`--since <24h>`), append bus status with `--consensus-decision`, store transcript under `_report/agent/<id>/consensus/`.
- Weekly manager review: rerun CLIs for trailing week, append receipt with `python -m tools.consensus.receipts --decision WEEKLY-<ISO>` and post summary in manager-report.
- Escalation: if a decision lacks receipts >24h, issue `bus_message --type request --meta escalation=consensus` tagging owner; track resolution next sweep.
- Docs touched: `docs/parallel-codex.md`, `docs/workflow.md` consensus sections.
