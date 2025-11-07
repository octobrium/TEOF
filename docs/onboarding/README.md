# Onboarding Landing (TEOF)

This is the canonical starting pane for new observers. Follow the sequence
below—each step must leave receipts before automation will promote you to the
next waypoint. Helper CLIs (`bin/teof-up`, `python -m tools.agent.doc_links …`)
mirror the same path so scripted onboarding stays consistent. For a single-page
loop summary (handshake → plan → bus → receipts), see the [`TEOF Operator Atlas`](../operator-atlas.md).

## Canonical First Hour
0. **Run the environment check (`bin/teof-syscheck`).**  
   Confirm Python, pip, and pytest are ready. Resolve issues *before* touching
   the repo.

1. **Read the map (`docs/architecture.md`).**  
   Understand placement rules, append-only contracts, and import boundaries.
   Capture a local note or memory receipt if anything blocks you—you will cite
   this file in every review.

2. **Load the workflow ladder (`docs/workflow.md`).**  
   Focus on `#architecture-gate-before-writing-code` and
   `#operator-mode-llm-quick-brief`. They explain why plans, receipts, and
   reversibility are non-negotiable.

3. **Seat your manifest (`docs/agents.md#files-to-know`).**  
   Copy the sample manifest into `AGENT_MANIFEST.json`, populate metadata, and
   keep it private. Automation refuses to run without a manifest.

4. **Execute the quickstart (`docs/quickstart.md`).**  
   Prefer the single command `bin/teof-up`; it installs the package, runs the
   smoke pipeline, and writes `_report/usage/onboarding/quickstart-*.json`.
   Inspect the receipt before proceeding. After a successful full run you can
   reuse the cached environment with `bin/teof-up --fast` to refresh receipts
   without rebuilding the wheel.

5. **Handshake on the bus (`docs/parallel-codex.md#suggested-session-loop`).**  
   Run `python3 -m tools.agent.session_boot --agent <id> --focus <role> --with-status`.
   This records the handshake, syncs the repo, captures `bus_status`, and writes
   the manager-report tail receipt required by preflight.

6. **Scaffold your first plan (`_plans/README.md`).**  
   Use `teof-plan new <slug> --summary "..." --scaffold` (or duplicate the
   template). Pair it with `python -m tools.receipts.main scaffold plan --plan-id <id>`
   so receipts exist before edits.

7. **Select work from the canonical backlog (`_plans/next-development.todo.json`).**  
   Choose the first item that matches your seat/systemic targets, seed the bus
   claim (`python -m tools.agent.bus_claim claim …`), then proceed into the plan.

Automation expects receipts from each step; if one is missing, preflight and CI
will instruct you to complete it before continuing.

## Session & Communication Loop
- **Manifest check** – confirm `AGENT_MANIFEST.json` lists the `agent_id` you
  will use on the bus (`python3 -m tools.agent.manifest_helper show`).
- **Announce the session** – `python3 -m tools.agent.session_boot --focus <role> --with-status`
  captures the handshake, manager-report tail, and coordination dashboard receipt.
- **Broadcast presence** – `python3 -m tools.agent.bus_message --task manager-report --type status --summary "<agent-id>: on deck for <focus>" --meta agent=<agent-id>`.
- **Monitor manager-report** – keep `python3 -m tools.agent.bus_watch --task manager-report --follow --limit 20`
  (or `python3 -m tools.agent.session_brief --task manager-report`) open while you work.
- **Claim and update** – use `python3 -m tools.agent.bus_claim claim`, `bus_event log --event status`, and `bus_message` to keep claims, plans, and receipts aligned.
- **Escalate & release** – escalate blockers with `bus_message --meta escalation=needed`, and close with `python3 -m tools.agent.bus_claim release --status done --summary "handoff"`.

## Operating Rhythm
- **Receipts-first** – no step is “done” until receipts exist. Record artifacts
  under `_report/agent/<id>/…`, cite them in the plan, and keep the
  [Receipts Map](../reference/receipts-map.md) handy.
- **Guardrails installed** – run `tools/hooks/install.sh` once per clone so
  pre-push hooks enforce receipts, planner validation, and targeted pytest.
- **Preflight every push** – `tools/agent/preflight.sh` mirrors the hook and
  refuses to run without the latest handshake or plan receipts.
- **Consolidate onboarding receipts** – run
  `python -m tools.agent.onboarding_check --agent <id>` after the first plan
  scaffold to capture status, task snapshot, and a summary JSON under
  `_report/onboarding/<id>/`.
- **Backlog discipline** – treat `_plans/next-development.todo.json`, your active
  plan, and `_bus/claims/` as the source of truth. Update plan steps before
  editing files and release the claim cleanly on handoff.
- **Respect memory** – review `memory/README.md` (use `teof memory summary` or
  `teof memory diff --run <id>`) before posting changes so you align with prior
  decisions.

## Command Quick Hits
| Need | Command | Reference |
| --- | --- | --- |
| Seat manifest | `python -m tools.agent.manifest_helper activate <id>` | `docs/agents.md#files-to-know` |
| Run quickstart | `bin/teof-up` (reuse with `--fast` after the first run) | `docs/onboarding/quickstart.md` |
| List onboarding docs | `python -m tools.agent.doc_links list --category onboarding` | `docs/quick-links.md` |
| Scaffold plan | `teof-plan new <slug> --summary "..." --scaffold` | `_plans/README.md#file-format-v0` |
| Scaffold plan receipts | `python -m tools.receipts.main scaffold plan --plan-id <id>` | `docs/automation.md#receipts-index` |
| Claim work | `python -m tools.agent.bus_claim claim --task <task> --plan <plan>` | `docs/parallel-codex.md#coordination-bus` |

## Related References
- `docs/workflow.md`, `docs/architecture.md`, and `docs/commandments.md` for the
  canonical governance contract.
- `docs/agents.md` for ongoing seat discipline (idle cadence, claim seeding,
  operator mode).
- `docs/parallel-codex.md` for coordination details and manager dashboards.
- `docs/reference/layer-guard-index.md` for the guard matrix.
- `docs/quick-links.md` + `python -m tools.agent.doc_links` when you need precise
  targets mid-session.

Keep this page aligned with automation and update it whenever the onboarding
sequence changes so newcomers land on the same S1/L0 footing.
