# TEOF Quick Reference

Use this sheet when you need citations fast. Each entry links to the canonical
source so you can jump straight to the definitive rule or command. For an end-to-end
loop summary (handshake → plan → bus → receipts), use the [`TEOF Operator Atlas`](../operator-atlas.md);
this page stays focused on pointers and lookup helpers.

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
For the core workflow commands and their receipts, see the [Operator Atlas command glossary](../operator-atlas.md#6-command-glossary-primary-loop). Use the table below for ancillary helpers.

| Action | Command | Note |
| --- | --- | --- |
| Seat manifest | `python -m tools.agent.manifest_helper activate <id>` | Validates `AGENT_MANIFEST.json` |
| Quickstart run | `bin/teof-up` | Installs package and emits onboarding receipts (reuse with `--fast` after the first run) |
| Preflight | `tools/agent/preflight.sh` | Runs receipts check, planner validate, targeted pytest |
| Doc quick links | `python -m tools.agent.doc_links list --category …` | Enumerates curated doc shortcuts |

Run `python -m tools.agent.doc_links list --category onboarding` or `python -m tools.agent.doc_links show <id>` when you need deeper detail—the entries map directly to the docs above.
