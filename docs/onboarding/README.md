# Onboarding Landing (TEOF)

Use this page as the single pane that unifies first-touch observation. Follow
the steps in order; each one leaves receipts so the next layer can trust you’ve
anchored properly. Automation mirrors this sequence (see `bin/teof-up`) and
prints the next waypoint after every receipt lands.

> **Adoption note:** If you are evaluating TEOF for a larger organisation, start with the README “Adoption snapshot” plus [`docs/architecture.md`](../architecture.md), [`docs/workflow.md`](../workflow.md), and [`docs/foundation/alignment-trail.md`](../foundation/alignment-trail.md). Those three surfaces explain the contract, operating cadence, and philosophical basis without forcing a full doc tour.

## Canonical First Hour
0. **Run the environment check (`bin/teof-syscheck`)**  
   Confirm Python, pip, and pytest are available before bootstrapping. Resolve
   any issues it reports before moving on.
1. **Frame the map (`docs/architecture.md`)**  
   Read the architecture contract start to finish. Capture a local note or
   memory receipt if something blocks placement—you will cite this file in every
   review.

2. **Load the operator ladder (`docs/workflow.md`)**  
   Focus on `#architecture-gate-before-writing-code` and `#operator-mode-llm-quick-brief`.
   These sections explain why plans, receipts, and reversibility are mandatory.

3. **Seat your manifest (`docs/agents.md#files-to-know`)**  
   Copy `docs/examples/agents/AGENT_MANIFEST.example.json` (or your assigned
   seat) to `AGENT_MANIFEST.json`, complete the metadata, and keep the file
   private. This unlocks guarded automation and makes session receipts valid.

4. **Execute the quickstart run (`docs/quickstart.md`)**  
   Prefer the single command `bin/teof-up`; it installs the package, runs the
   smoke pipeline, and writes `_report/usage/onboarding/quickstart-*.json`.
   Inspect the receipt before moving forward.

5. **Handshake on the bus (`.github/AGENT_ONBOARDING.md`)**  
   Run `python -m tools.agent.session_boot --agent <id> --focus <role> --with-status`
   and follow the manager-report loop in `docs/parallel-codex.md#suggested-session-loop`.
   Don’t claim work until the handshake receipt exists.

6. **Scaffold your first plan (`_plans/README.md`)**  
   Create a plan skeleton with `teof-plan new <slug> --summary "..." --scaffold`
   or duplicate `_plans/1970-01-01-agent-template.plan.json`. Pair it with
   `python -m tools.receipts.main scaffold plan --plan-id <id>` so the receipts
   directory exists before edits.

7. **Select work from the canonical backlog (`_plans/next-development.todo.json`)**  
   Choose the first item that matches your seat/systemic targets, seed the bus
   claim (`python -m tools.agent.bus_claim claim …`), then proceed into the plan.

Each step depends on the previous receipts; if automation can’t find them, it
will prompt you to back up and finish the chain. When the sequence changes,
update this file and the helpers that announce the “next doc” so new agents
stay synchronized.

## Daily Loop Reminders
- **Receipts before commits:** `python -m tools.receipts.main status` surfaces
  missing artifacts; `python -m tools.agent.session_brief --preset operator`
  captures the context manager-report expects.
- **Backlog discipline:** prioritize `_plans/next-development.todo.json`, keep
  your plan status truthful, and release claims cleanly on handoff.
- **Preflight every push:** `tools/agent/preflight.sh` mirrors the pre-push hook
  and fails fast on absent plans, receipts, or bus tail evidence.
- **Stay on the bus:** keep `python -m tools.agent.bus_watch --follow` running
  and refresh claims via `python -m tools.agent.bus_claim` / `bus_event` /
  `bus_message` as you progress.
- **Respect memory:** review `memory/README.md` and use `teof memory summary`
  (or `teof memory diff --run <id>`) before posting changes so you align with
  prior decisions.

## Command Quick Hits
| Need | Command | Reference |
| --- | --- | --- |
| Seat manifest | `python -m tools.agent.manifest_helper activate <id>` | `docs/agents.md#files-to-know` |
| Run quickstart | `bin/teof-up` | `docs/onboarding/quickstart.md` |
| List onboarding docs | `python -m tools.agent.doc_links list --category onboarding` | `docs/quick-links.md` |
| Scaffold plan | `teof-plan new <slug> --summary "..." --scaffold` | `_plans/README.md#file-format-v0` |
| Scaffold plan receipts | `python -m tools.receipts.main scaffold plan --plan-id <id>` | `docs/automation.md#receipts-index` |
| Claim work | `python -m tools.agent.bus_claim claim --task <task> --plan <plan>` | `docs/parallel-codex.md#coordination-bus` |

## When You Need More
- `.github/AGENT_ONBOARDING.md` for the narrated first-session checklist and
  operating rhythm reminders.
- `docs/quick-links.md` plus `python -m tools.reference.lookup` for targeted
  lookups once the base receipts are in place.
- `docs/parallel-codex.md` for deep coordination policy, manager dashboards, and
  follow-up logging.
- `docs/agents.md` for ongoing seat discipline (idle cadence, claim seeding,
  operator mode).
- `docs/reference/layer-guard-index.md` for the fast mapping from layers to the
  exact scripts/tests that enforce them.

Keep this page aligned with automation so every new observer lands on the same
S1/L0 footing.
