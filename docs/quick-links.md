# Docs Quick Links

This index mirrors `docs/quick-links.json` and powers `python -m tools.agent.doc_links`. Use it when you need to land on a governance anchor quickly without scanning multiple files.

## Helper CLI
- List everything: `python -m tools.agent.doc_links list`
- Emit JSON (for scripts/receipts): `python -m tools.agent.doc_links list --format json`
- Show one entry: `python -m tools.agent.doc_links show <id>`

## Canonical Entries
| id | title | summary | target |
| --- | --- | --- | --- |
| `agents-claim-seeding` | Claim Seeding (Managers) | Manager flow for staging claims before assignments so auto-claim succeeds. | [docs/AGENTS.md#claim-seeding-managers](docs/AGENTS.md#claim-seeding-managers) |
| `agents-idle-cadence` | Idle Cadence | Idle escalation loop for agents broadcasting availability and claiming work. | [docs/AGENTS.md#idle-cadence](docs/AGENTS.md#idle-cadence) |
| `bus-claims-schema` | Claim File Schema | Schema for `_bus/claims/<task>.json` guarded by automation and CI. | [_bus/README.md#claim-file-schema-_busclaimstask_idjson](_bus/README.md#claim-file-schema-_busclaimstask_idjson) |
| `capsule-cadence` | Capsule Release Cadence | Follow the freeze/release checklist using coordination dashboard, plan hygiene, and anchors. | [docs/maintenance/capsule-cadence.md#capsule-release-cadence](docs/maintenance/capsule-cadence.md#capsule-release-cadence) |
| `capsule-status-ledger` | Capsule Status Ledger | Snapshot of the active capsule, required receipts, and verification commands. | [docs/maintenance/capsule-status-ledger.md#capsule-status-ledger](docs/maintenance/capsule-status-ledger.md#capsule-status-ledger) |
| `collab-support-offer-help` | Monitor & Offer Help | Live support loop for idle agents watching the bus and responding to blockers. | [docs/collab-support.md#2-monitor--offer-help](docs/collab-support.md#2-monitor--offer-help) |
| `comm-mainline` | Communication Quickstart | Shows how to claim, broadcast, and monitor the coordination bus (manager-report) on day one. | [.github/AGENT_ONBOARDING.md#communication-quickstart-manager-report-hub](.github/AGENT_ONBOARDING.md#communication-quickstart-manager-report-hub) |
| `comm-directive-pointer` | Directive Pointer Helper | Run `tools.agent.directive_pointer` so BUS-COORD directives automatically mirror into manager-report. | [docs/AGENTS.md#idle-cadence](docs/AGENTS.md#idle-cadence) |
| `decision-hierarchy` | Decision Hierarchy | Map governance objectives before downstream work becomes decidable. | [docs/decision-hierarchy.md](docs/decision-hierarchy.md) |
| `proposal-inbox` | Proposal Inbox | Canonical drop zone for draft improvements awaiting review. | [docs/proposals/README.md#proposal-inbox-docsproposals](docs/proposals/README.md#proposal-inbox-docsproposals) |
| `emergent-principles-ledger` | Emergent Principles Ledger | Append lessons to reuse patterns before automating. | [governance/core/emergent-principles.jsonl](governance/core/emergent-principles.jsonl) |
| `consensus-ledger` | Consensus Ledger Usage | Entry point for `tools.consensus.ledger` commands and receipt capture. | [docs/consensus/README.md#usage](docs/consensus/README.md#usage) |
| `consensus-ci-summary` | Consensus CI Guard | Stable receipts + CI check ensuring QUEUE-030..033 stay covered. | [_report/consensus/summary-latest.json](_report/consensus/summary-latest.json) |
| `capsule-cadence-summary` | Capsule Cadence Guard | Release checklist tied to consensus receipts and capsule hashes. | [_report/capsule/summary-latest.json](_report/capsule/summary-latest.json) |
| `receipts-index` | Receipts Index CLI | Build a JSONL ledger of plans, receipts, and manager messages before handoff. | [docs/automation.md#receipts-index](docs/automation.md#receipts-index) |
| `receipts-latency` | Receipts Latency Metrics | Compute deltas between reflections and receipts using the ledger. | [docs/automation.md#receipts-latency](docs/automation.md#receipts-latency) |
| `coordination-dashboard` | Coordination Dashboard | Run the aggregated snapshot CLI for plans, claims, and heartbeat alerts. | [docs/parallel-codex.md#coordination-dashboard](docs/parallel-codex.md#coordination-dashboard) |
| `onboarding-first-session` | First Session Checklist | Seat-up instructions for pairing the repo checkout with governance rails on day one. | [.github/AGENT_ONBOARDING.md#first-session-checklist](.github/AGENT_ONBOARDING.md#first-session-checklist) |
| `onboarding-rhythm` | Operating Rhythm | Daily cadence reminder covering receipts discipline, hooks, and preflight guardrails. | [.github/AGENT_ONBOARDING.md#operating-rhythm](.github/AGENT_ONBOARDING.md#operating-rhythm) |
| `parallel-follow-ups` | Follow-up Logging | How to close manager follow-ups with mirrored bus events and receipts. | [docs/parallel-codex.md#follow-up-logging](docs/parallel-codex.md#follow-up-logging) |
| `parallel-session-loop` | Suggested Session Loop | Canonical 13-step loop covering sync, bus traffic, planning, and release. | [docs/parallel-codex.md#suggested-session-loop](docs/parallel-codex.md#suggested-session-loop) |
| `plans-schema` | Plan File Format (v0) | Planner contract describing required fields, receipts, and lifecycle. | [_plans/README.md#file-format-v0](_plans/README.md#file-format-v0) |
| `quickstart-agents-bootstrap` | Agent Bootstrap | One-minute agent bootstrap snippet with install + teof brief. | [docs/AGENTS.md#bootstrap-one-minute](docs/AGENTS.md#bootstrap-one-minute) |
| `quickstart-readme` | Quickstart (README) | Root README snippet: install locally then run `teof brief`. | [README.md#quickstart](README.md#quickstart) |
| `quickstart-smoke` | Quickstart Smoke | Install locally then run `teof brief` to produce OCERS receipts under artifacts/ocers_out/ | [docs/quickstart.md#quickstart](docs/quickstart.md#quickstart) |
| `reconciliation-pipeline` | Reconciliation Pipeline | Run hello/diff/fetch/merge via `python -m tools.reconcile_pipeline` (supports --fail-on-diff). | [docs/cli.md#reconciliation-pipeline](docs/cli.md#reconciliation-pipeline) |
| `workflow-architecture` | Architecture Gate | Explains the governance gate that blocks edits without a plan and receipts. | [docs/workflow.md#architecture-gate-before-writing-code](docs/workflow.md#architecture-gate-before-writing-code) |
| `workflow-receipts` | DNA Recursion (Receipts) | Details the receipts-first mandate used by manager directives and CI guards. | [docs/workflow.md#dna-recursion-self-improvement-of-the-rules](docs/workflow.md#dna-recursion-self-improvement-of-the-rules) |
| `ci-guardrails` | CI Guardrail Guarantees | One-screen summary mapping invariants to the scripts that enforce them. | [docs/ci-guarantees.md#ci-guardrail-guarantees](docs/ci-guarantees.md#ci-guardrail-guarantees) |


_Last updated: 2025-09-21
