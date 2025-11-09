# Impact Ledger (O4)

Documenting real-world outcomes attributable to TEOF activity. Each entry links
to supporting receipts (prompts, reflections, artifacts) so success can be
audited.

## Template
```
Date: <YYYY-MM-DD>
Outcome: <What happened (e.g., published article, closed deal)>
Value: <Quantified impact (revenue, hours saved, opportunity created)>
Receipts:
  - <memory/reflections/...>
  - <_report/...>
Notes: <Context, lessons learned>
```

Record raw entries with `python3 -m tools.receipts.log_event impact --title ...`
(writes to `memory/impact/log.jsonl`); summarize key wins here for storytelling.

## Automation bridge

- Every plan must declare an `impact_ref` that matches a slug in `memory/impact/log.jsonl`. Reuse the slug when closing work that fulfilled a ledger entry or mint a new slug alongside the ledger update.
- Run `python3 -m teof impact_bridge --report-dir _report/impact/bridge --fail-on-missing` to emit JSON + markdown dashboards tying ledger entries to backlog items, plans, and receipts. The CLI prints a stats summary by default; add `--format json` for machine-readable stdout and `--orphans-out _report/impact/bridge/orphans.json` when you want a ready-made remediation queue.
- Review `_report/impact/bridge/impact-bridge-*.json` before marking a backlog objective done; the summary shows which Meaning-level outcomes still lack traceable plan receipts.

## Example Entries

- *2025-09-23 — API Relay Dry-Run Pilot*
  - Outcome: Guarded conduit for external agent responses.
  - Value: Enables future monetization via automated research/drafting.
  - Receipts: `_report/usage/autonomy-conductor/api-relay/relay-conductor-20250923T204918Z.json`, `memory/reflections/reflection-20250923T205003Z.json`.
  - Notes: Dry-run only; follow-up to enable live calls and monetizable outputs.
- *2025-09-26 — Objectives Instrumentation for Relay Insight Sprint*
  - Outcome: Ledger + conductor receipts now capture coordination docs, impact cadence, and multi-agent participation so sales collateral can cite deterministic guardrails.
  - Value: Pre-revenue (unlocking Tier A/B pricing conversations).
  - Receipts: `tools/autonomy/objectives_status.py`, `tools/autonomy/conductor.py`, `docs/vision/objectives-ledger.md`, `docs/automation/autonomy-conductor.md`.
  - Notes: Enables quoting prospects with concrete guardrail evidence ahead of the Relay Insight Sprint pilot.

- *2025-10-03 — Relay Insight Sprint Case Study*
  - Outcome: First client-facing relay sprint published with verifiable receipts and public brief.
  - Value: 0.0 (pipeline cred)
  - Receipts: `_report/usage/case-study/relay-insight/summary.json`, `docs/impact/relay-insight-public.md`, `docs/impact/relay-insight-case-study.md`, `_report/usage/case-study/relay-insight/conductor-run-20251003T191500Z.json`
  - Notes: Case study closes ND-014/ND-016 by tying conductor runs, guarded commands, and ledger updates together for sales collateral.
