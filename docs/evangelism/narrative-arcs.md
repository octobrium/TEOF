# Narrative Arcs

Every arc maps to L2 Objective O3 (shared mental model) and O4 (impact feedback). Pick the arc that matches the listener and link the receipts below.

## Arc A — Receipts-First Autonomy
- **Audience:** engineering leaders who demand verifiable guardrails before trusting automation.
- **Thesis:** TEOF only advances when authenticity, plan hygiene, and objectives snapshots are green. The conductor prompt shows this in one glance.
- **Proof Points:**
  - Autonomy conductor receipt with trust scores and guardrails (`_report/usage/autonomy-conductor/conductor-20250927T195724Z.json`).
  - Autonomy preflight summary that pairs planner validation with the same trust data (`_report/usage/autonomy-preflight/preflight-20250927T200419Z.json`).
  - Workflow architecture gate (`docs/workflow.md#architecture-gate-before-writing-code`).
- **Call to Action:** invite them to run `teof brief` then inspect the receipts directory to see the same contract locally.

## Arc B — Authenticity as a Safety Net
- **Audience:** compliance, risk, and governance stakeholders.
- **Thesis:** authenticity tiers stay above threshold and trigger assignments when drift appears; receipts prove the escalation loop already works.
- **Proof Points:**
  - Authenticity summary referenced in external monitor output (`_report/usage/external-summary.json`).
  - Objectives ledger capturing O5 guardrail integrity (`docs/vision/objectives-ledger.md`).
  - Assignment record for authenticity guard follow-up (`_bus/assignments/AUTH-PRIMARY_TRUTH-codex-5-20250922.json`).
- **Call to Action:** walk them through the escalation history in `_bus/events/events.jsonl` filtered by `AUTH-PRIMARY_TRUTH` and offer ongoing alerts.

## Arc C — Cooperative Cadence
- **Audience:** product and partnership teams evaluating collaboration health.
- **Thesis:** multiple neurons can join mid-stream, claim work, and stay in lockstep because the bus, plans, and coordination dashboard speak the same language.
- **Proof Points:**
  - Parallel Codex coordination guide (`docs/parallel-codex.md#coordination-dashboard`).
  - Manager heartbeat receipts that sample the dashboard output (`_report/agent/codex-4/2025-09-19-heartbeat-integration-codex4/coord-dashboard.json`).
  - Multi-neuron playbook describing onboarding rhythm (`docs/vision/multi-neuron-playbook.md`).
- **Call to Action:** offer a dry-run session using `python -m tools.agent.session_boot` so they see claims, events, and dashboards update in real time.
