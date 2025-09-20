# Agent Onboarding (TEOF)

Purpose: give a new human + LLM pair the minimum set of rails to join TEOF safely while staying inside the governance policy.

## First Session Checklist
1. **Prep access** – issue a read-scoped credential (GitHub App or PAT) and sandbox the checkout. Only upgrade to write access for `agent/<id>/*` branches after review. (See `docs/workflow.md#non-negotiables-apply-to-every-change`.)
2. **Read the rails** – follow the architecture/workflow overview (`docs/workflow.md#architecture-gate-before-writing-code`) and receipts discipline (`docs/workflow.md#dna-recursion-self-improvement-of-the-rules`) before touching code.
3. **Capture your manifest** – copy `AGENT_MANIFEST.example.json` → `AGENT_MANIFEST.json`, fill in metadata, and store locally. Reference: `docs/AGENTS.md#files-to-know`.
4. **Plan before edits** – duplicate `_plans/1970-01-01-agent-template.plan.json`, add a justification, and log the plan per `docs/AGENTS.md#contract`. Prefer `teof-plan new <slug> --summary "..." --scaffold` (fallback: `python3 -m tools.planner.cli new ...`) so the receipt folder is created immediately.
5. **Run the Quickstart smoke** – verify your checkout produces canonical artifacts before touching new work.
<!-- generated: quickstart snippet -->
See [`docs/quickstart.md#quickstart`](../docs/quickstart.md#quickstart) for the canonical smoke test commands (`python3 -m pip install -e .`, `teof brief`, `ls artifacts/ocers_out/latest`, `cat artifacts/ocers_out/latest/brief.json`) and the notes on receipts under `artifacts/ocers_out/<UTC>`. Need quick references? `python -m tools.agent.doc_links list --category quickstart` points to the same section.

6. **Announce + claim** – run `python3 -m tools.agent.session_boot --agent <id> --focus <role> --with-status` and follow the coordination loop in `docs/parallel-codex.md#suggested-session-loop` (auto-claiming via task assignments when available). The helper logs a handshake and captures a `bus_status` summary receipt for you.
   - When swapping seats, capture your branch + manifest with `python -m tools.agent.manifest_helper session-save <label>` and restore them later with `... session-restore <label>`.

## Communication Quickstart (manager-report hub)
- **Verify your manifest** – confirm `AGENT_MANIFEST.json` (or `python3 -m tools.agent.manifest_helper show`) lists the `agent_id` you’ll use on the bus.
- **Announce the session** – `python3 -m tools.agent.session_boot --agent <agent-id> --focus <role> --with-status` records the handshake, syncs the repo, and captures a `bus_status` receipt.
- **Broadcast the hello** – post on the shared lane: `python3 -m tools.agent.bus_message --task manager-report --type status --summary "<agent-id>: on deck for <focus>" --meta agent=<agent-id>`.
- **Open directives with a pointer** – `python3 -m tools.agent.directive_pointer --task BUS-COORD-xxxx --summary "<directive summary>" --plan <plan-id>` writes the directive entry and mirrors it in `manager-report` so every seat sees the update.
- **Remember the guard** – the bus refuses mismatched ids; if `--agent` disagrees with `AGENT_MANIFEST.json` run `session_boot` or `manifest_helper activate` before posting.
- **Confirm visibility** – keep the feed in view with `python3 -m tools.agent.bus_watch --task manager-report --follow --limit 20` (or spot-check via `python3 -m tools.agent.session_brief --task manager-report --limit 5`).
- **Continue coordination** – run the core commands as you work:
  - Claim work: `python3 -m tools.agent.bus_claim claim --task <task_id> --plan <plan_id>`
  - Send status heartbeats: `python3 -m tools.agent.bus_event log --event status --task <task_id> --summary "<agent-id> working" --plan <plan_id> [--receipt <path>]`
  - Shortcut heartbeat: `python3 -m tools.agent.bus_ping --task <task_id> --message-task <task_id> --summary "working"` (auto-prefixes `<agent-id>:` and hits both logs; add `--skip-message` if you only need the event).
  - Reply on task threads: `python3 -m tools.agent.bus_message --task <task_id> --type status --summary "<update>" --receipt <path> --meta agent=<agent-id>`
  - Escalate blockers: `python3 -m tools.agent.bus_message --task <task_id> --type status --meta escalation=needed --summary "<agent-id>: still blocked"`
  - Close the loop: `python3 -m tools.agent.bus_claim release --task <task_id> --status done --summary "handoff"`

## Operating Rhythm
- **Receipts-first** – no step is “done” until receipts exist. Record artifacts under `_report/agent/<id>/…` and cite them in the plan. (Governance anchor: `docs/workflow.md#architecture-gate-before-writing-code`.) Use `--scaffold` on `tools.agent.task_assign`, `tools.agent.claim_seed`, or `teof-plan new` to generate the skeleton on day zero.
- **Install the guard hook once per clone** – run `tools/hooks/install.sh` to wire the repo-managed pre-push hook (it runs receipts check, planner validation, and targeted pytest before every push).
- **Preflight every push** – run `tools/agent/preflight.sh` before pushing or requesting review; it mirrors the hook (receipts, plan guard, planner validate, bus status, targeted pytest) and enforces the manager directive in `_bus/messages/manager-report.jsonl`.
- **Stay on the bus** – log progress with `python3 -m tools.agent.bus_event log --event status …`, respond to manager notes in `_bus/messages/<task>.jsonl`, and monitor peers via `docs/parallel-codex.md#self-audit` (`python -m tools.agent.bus_watch --follow` or `python -m tools.agent.bus_status --preset support --agent <id>` for quick snapshots).
- **Use clear summaries** – prefix every bus message summary with your actual `agent_id` (`<agent-id>:`) so manifests, manager-report, and receipts stay aligned.
- **Refresh heartbeat on sweeps** – managers should append `--log-heartbeat` when running `python -m tools.agent.manager_report` so the bus knows they are active (customise the text with `--heartbeat-summary`; tag metadata via `--heartbeat-meta key=value` or the shortcut `--heartbeat-shift <label>`).
- **Close cleanly** – release the claim (`python3 -m tools.agent.bus_claim release …`) and refresh the handshake when wrapping up (`session_boot --summary "session wrap" --focus idle`).

## Where to Go Deeper
- **Quick links** – `python -m tools.agent.doc_links list` (use `... show <id>` for details; manifest lives in `docs/quick-links.md`) for a canonical index of guidance surfaces.
- **Daily rhythms** – `docs/AGENTS.md` for idle cadence, claim seeding, and optional role coordination.
- **Multi-agent coordination** – `docs/parallel-codex.md` for detailed bus usage, follow-up logging, and consensus tooling.
- **Tooling reference** – `_plans/README.md` (plan schema), `_bus/README.md` (claims/events), `tools/agent/runner.sh` (optional helper).

## Policy Anchors
- `governance/policy.json`
- `docs/workflow.md`
- `docs/architecture.md`

Receipts, reversibility, and strict planner validation keep the network auditable—treat this page as the lightweight pointer to those canonical sources.
