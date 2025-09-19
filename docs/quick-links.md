# Docs Quick Links

This index mirrors `docs/quick-links.json` and powers `python -m tools.agent.doc_links`. Use it when you need to land on a governance anchor quickly without scanning multiple files.

## Helper CLI
- List everything: `python -m tools.agent.doc_links list`
- Emit JSON (for scripts/receipts): `python -m tools.agent.doc_links list --format json`
- Show one entry: `python -m tools.agent.doc_links show <id>`

## Canonical Entries
| id | title | summary | target |
| --- | --- | --- | --- |
| `onboarding-first-session` | First Session Checklist | Seat-up instructions for pairing the repo checkout with governance rails on day one. | [.github/AGENT_ONBOARDING.md#first-session-checklist](.github/AGENT_ONBOARDING.md#first-session-checklist) |
| `onboarding-rhythm` | Operating Rhythm | Daily cadence reminder covering receipts discipline, hooks, and preflight guardrails. | [.github/AGENT_ONBOARDING.md#operating-rhythm](.github/AGENT_ONBOARDING.md#operating-rhythm) |
| `workflow-architecture` | Architecture Gate | Explains the governance gate that blocks edits without a plan and receipts. | [docs/workflow.md#architecture-gate-before-writing-code](docs/workflow.md#architecture-gate-before-writing-code) |
| `workflow-receipts` | DNA Recursion (Receipts) | Details the receipts-first mandate used by manager directives and CI guards. | [docs/workflow.md#dna-recursion-self-improvement-of-the-rules](docs/workflow.md#dna-recursion-self-improvement-of-the-rules) |
| `agents-idle-cadence` | Idle Cadence | Idle escalation loop for agents broadcasting availability and claiming work. | [docs/AGENTS.md#idle-cadence](docs/AGENTS.md#idle-cadence) |
| `agents-claim-seeding` | Claim Seeding (Managers) | Manager flow for staging claims before assignments so auto-claim succeeds. | [docs/AGENTS.md#claim-seeding-managers](docs/AGENTS.md#claim-seeding-managers) |
| `parallel-session-loop` | Suggested Session Loop | Canonical 13-step loop covering sync, bus traffic, planning, and release. | [docs/parallel-codex.md#suggested-session-loop](docs/parallel-codex.md#suggested-session-loop) |
| `parallel-follow-ups` | Follow-up Logging | How to close manager follow-ups with mirrored bus events and receipts. | [docs/parallel-codex.md#follow-up-logging](docs/parallel-codex.md#follow-up-logging) |
| `coordination-dashboard` | Coordination Dashboard | Run the aggregated snapshot CLI for plans, claims, and heartbeat alerts. | [docs/parallel-codex.md#coordination-dashboard](docs/parallel-codex.md#coordination-dashboard) |
| `collab-support-offer-help` | Monitor & Offer Help | Live support loop for idle agents watching the bus and responding to blockers. | [docs/collab-support.md#2-monitor--offer-help](docs/collab-support.md#2-monitor--offer-help) |
| `bus-claims-schema` | Claim File Schema | Schema for `_bus/claims/<task>.json` guarded by automation and CI. | [_bus/README.md#claim-file-schema-_busclaimstask_idjson](_bus/README.md#claim-file-schema-_busclaimstask_idjson) |
| `plans-schema` | Plan File Format (v0) | Planner contract describing required fields, receipts, and lifecycle. | [_plans/README.md#file-format-v0](_plans/README.md#file-format-v0) |
| `consensus-ledger` | Consensus Ledger Usage | Entry point for `tools.consensus.ledger` commands and receipt capture. | [docs/consensus/README.md#usage](docs/consensus/README.md#usage) |

_Last updated: 2025-09-19_
