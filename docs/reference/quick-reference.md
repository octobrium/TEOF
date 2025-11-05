# TEOF Quick Reference

Use this sheet when you need citations fast. Each entry links to the canonical
source so you can jump straight to the definitive rule or command.

## Foundations
- **Architecture map:** `docs/architecture.md`
- **Workflow gate:** `docs/workflow.md#architecture-gate-before-writing-code`
- **Receipts discipline:** `docs/workflow.md#dna-recursion-self-improvement-of-the-rules`
- **Commandments:** `docs/commandments.md`
- **Alignment protocol (TAP):** `docs/foundation/alignment-protocol/tap.md`

## Coordination & Claims
- **First session loop:** `.github/AGENT_ONBOARDING.md#communication-quickstart-manager-report-hub`
- **Suggested ongoing loop:** `docs/parallel-codex.md#suggested-session-loop`
- **Claim schema:** `_bus/README.md#claim-file-schema-_busclaimstask_idjson`
- **Event logging:** `docs/parallel-codex.md#coordination-bus`
- **Manager dashboard:** `docs/parallel-codex.md#coordination-dashboard`

## Plans, Receipts, Memory
- **Plan schema:** `_plans/README.md#file-format-v0`
- **Scaffold helpers:** `docs/automation.md#receipts-index`
- **Receipts hygiene bundle:** `docs/automation.md#receipts-hygiene-bundle`
- **Memory usage:** `memory/README.md`
- **Receipts map:** `docs/reference/receipts-map.md`

## Backlog & Queue
- **Source of truth:** `docs/backlog.md`
- **Next Development list:** `_plans/next-development.todo.json`
- **Claim files:** `_bus/claims/`

## Automation Commands
| Action | Command | Source |
| --- | --- | --- |
| Seat manifest | `python -m tools.agent.manifest_helper activate <id>` | `docs/agents.md#files-to-know` |
| Session boot | `python -m tools.agent.session_boot --agent <id> --focus <role> --with-status` | `.github/AGENT_ONBOARDING.md#communication-quickstart-manager-report-hub` |
| Claim task | `python -m tools.agent.bus_claim claim --task <task> --plan <plan>` | `docs/parallel-codex.md#coordination-bus` |
| Emit heartbeat | `python -m tools.agent.bus_event log --event status --task <task> --summary "..."` | `docs/parallel-codex.md#coordination-bus` |
| Quickstart run | `bin/teof-up` | `docs/onboarding/quickstart.md` |
| Preflight | `tools/agent/preflight.sh` | `.github/AGENT_ONBOARDING.md#operating-rhythm` |
| Reference search | `python -m tools.reference.lookup <topic>` | `docs/reference/quick-reference.md` |

## Philosophy & Prompts
- **Meaning & purpose passages:** `docs/foundation/alignment-protocol/tap.md#meaning`, `docs/whitepaper.md#purpose`
- **Trust / observer framing:** `docs/foundation/alignment-protocol/tap.md#observer`, `docs/workflow.md#observation-primacy`
- **Prompt helper:** `python -m tools.prompts.philosophy "<question>"` (emits `_report/usage/prompts/` receipts)

## Related Helpers
- **Onboarding landing:** `docs/onboarding/README.md`
- **Agent discipline:** `docs/agents.md`
- **Quick links manifest:** `docs/quick-links.md`
- **Doc links CLI:** `python -m tools.agent.doc_links list --category onboarding`

Run `python -m tools.reference.lookup` with keywords (for example `lookup quickstart`)
when you need the matching lines from this sheet inside the terminal.
