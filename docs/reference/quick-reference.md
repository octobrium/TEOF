# TEOF Quick Reference

Use this sheet when you need citations fast. Each entry links to the canonical
source so you can jump straight to the definitive rule or command.

## Canonical Docs
- `docs/architecture.md` — placement rules and append-only contracts.
- `docs/workflow.md` — operating ladder, planner discipline, receipts policy.
- `docs/commandments.md` — fast trust contract.
- `docs/onboarding/README.md` — first-hour sequence, communication loop, daily rhythm.
- `docs/reference/receipts-map.md` — canonical receipt lanes.
- `docs/parallel-codex.md` — coordination policy, manager dashboards, bus usage.

## Operational References
- Plans and backlog: `_plans/README.md`, `_plans/next-development.todo.json`.
- Claims and events: `_bus/README.md`.
- Agents & manifests: `docs/agents.md`.
- Memory discipline: `memory/README.md`.
- Automation receipts: `docs/automation.md` (index, latency, hygiene bundles).

## Lookup & Tooling
- Quick links manifest: `docs/quick-links.md` (drive with `python -m tools.agent.doc_links ...`).
- Guard index: `docs/reference/layer-guard-index.md`.
- Keyword lookup: `python -m tools.reference.lookup <keyword>`.
- Prompt helper: `python -m tools.prompts.philosophy "<question>"` (writes `_report/usage/prompts/`).

## Common Commands
| Action | Command | Note |
| --- | --- | --- |
| Seat manifest | `python -m tools.agent.manifest_helper activate <id>` | Validates `AGENT_MANIFEST.json` |
| Session boot | `python -m tools.agent.session_boot --agent <id> --focus <role> --with-status` | Captures handshake + manager-report tail |
| Claim work | `python -m tools.agent.bus_claim claim --task <task> --plan <plan>` | Mirrors `_bus/claims/<task>.json` |
| Quickstart run | `bin/teof-up` | Installs package and emits onboarding receipts |
| Preflight | `tools/agent/preflight.sh` | Runs receipts check, planner validate, targeted pytest |
| Plan scaffold | `teof-plan new <slug> --summary "..." --scaffold` | Creates plan + receipt folder |

Run `python -m tools.agent.doc_links list --category onboarding` or `python -m tools.agent.doc_links show <id>` when you need deeper detail—the entries map directly to the docs above.
