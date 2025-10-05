# Onboarding Landing (TEOF)

Use this page as the single screen to get oriented. It links the minimum surfaces
needed for a productive first session and shows where to deepen later.

## First Hour Path
1. **Absorb the rails** – read `docs/architecture.md` (map) then
   `docs/workflow.md#architecture-gate-before-writing-code` and
   `docs/workflow.md#dna-recursion-self-improvement-of-the-rules` to understand
   why plans, receipts, and reversibility are mandatory.
2. **Seat your manifest** – copy `docs/examples/agents/AGENT_MANIFEST.example.json`
   (or another seat) to `AGENT_MANIFEST.json`, fill in your metadata, and keep it
   private. Reference: `docs/agents.md#files-to-know`.
3. **Spin the quickstart** – follow the short run in
   `docs/quickstart.md#quickstart`. Prefer `bin/teof-up` for the single command
   path; fall back to the two-command sequence in `docs/onboarding/quickstart.md`
   when you need to inspect each step.
4. **Announce & claim** – run `python -m tools.agent.session_boot --agent <id>
   --focus <role> --with-status`, then follow the coordination loop at
   `.github/AGENT_ONBOARDING.md#communication-quickstart-manager-report-hub` and
   `docs/parallel-codex.md#suggested-session-loop`.
5. **Scaffold your plan** – duplicate `_plans/1970-01-01-agent-template.plan.json`
   or run `teof-plan new <slug> --summary "..." --scaffold` so the receipts
   folder exists before edits.

## Daily Loop Reminders
- **Stay receipts-first:** `python -m tools.receipts.main status` shows missing
  artifacts; `python -m tools.agent.session_brief --preset operator` captures
  what the manager preflight checks expect.
- **Guardrails before push:** `tools/agent/preflight.sh` mirrors the pre-push
  hook (`tools/hooks/install.sh`) and fails fast on missing plans, receipts, or
  bus tail evidence.
- **Coordination traffic:** keep `python -m tools.agent.bus_watch --follow`
  running and refresh claims via `python -m tools.agent.bus_claim` / `bus_event`
  / `bus_message` as you progress.
- **Memory alignment:** inspect `memory/README.md` and use `teof memory summary`
  or `teof memory diff --run <id>` before responding so you do not contradict
  prior sessions.

## Command Quick Hits
| Need | Command | Reference |
| --- | --- | --- |
| Seat manifest | `python -m tools.agent.manifest_helper activate <id>` | `docs/agents.md#files-to-know` |
| Run quickstart | `bin/teof-up` | `docs/onboarding/quickstart.md` |
| List docs | `python -m tools.agent.doc_links list --category onboarding` | `docs/quick-links.md` |
| Lookup quick ref | `python -m tools.reference.lookup <topic>` | `docs/reference/quick-reference.md` |
| Scaffold plan | `teof-plan new <slug> --summary "..." --scaffold` | `_plans/README.md#file-format-v0` |
| Capture receipts | `python -m tools.receipts.main scaffold plan --plan-id <id>` | `docs/automation.md#receipts-index` |
| Claim work | `python -m tools.agent.bus_claim claim --task <task> --plan <plan>` | `docs/parallel-codex.md#coordination-bus` |

## When You Need More
- `.github/AGENT_ONBOARDING.md` for the narrated first-session checklist and
  operating rhythm reminders.
- `docs/agents.md` for ongoing agent discipline (idle cadence, claim seeding,
  operator mode).
- `docs/parallel-codex.md` for deep coordination policy, manager dashboards, and
  follow-up logging.
- `docs/reference/quick-reference.md` for the expandable links catalogue (works
  with `python -m tools.reference.lookup`).
- `docs/quick-links.md` for the canonical quick link manifest used by automation
  (`python -m tools.agent.doc_links`).

Keep this page updated as the tooling surface evolves so newcomers always have a
single entry point.
