# Agent Onboarding (TEOF)

Purpose: give a new human + LLM pair the minimum set of rails to join TEOF safely while staying inside the governance policy.

## First Session Checklist
1. **Prep access** – issue a read-scoped credential (GitHub App or PAT) and sandbox the checkout. Only upgrade to write access for `agent/<id>/*` branches after review. (See `docs/workflow.md#non-negotiables-apply-to-every-change`.)
2. **Read the rails** – follow the architecture/workflow overview (`docs/workflow.md#architecture-gate-before-writing-code`) and receipts discipline (`docs/workflow.md#dna-recursion-self-improvement-of-the-rules`) before touching code.
3. **Capture your manifest** – copy `AGENT_MANIFEST.example.json` → `AGENT_MANIFEST.json`, fill in metadata, and store locally. Reference: `docs/AGENTS.md#files-to-know`.
4. **Plan before edits** – duplicate `_plans/1970-01-01-agent-template.plan.json`, add a justification, and log the plan per `docs/AGENTS.md#contract`. Prefer `python3 -m tools.planner.cli new <slug> --summary "..." --scaffold` so the receipt folder is created for you immediately.
5. **Announce + claim** – run `python3 -m tools.agent.session_boot --agent <id> --focus <role> --with-status` and follow the coordination loop in `docs/parallel-codex.md#suggested-session-loop` (auto-claiming via task assignments when available). The helper logs a handshake and captures a `bus_status` summary receipt for you.
   - When swapping seats, capture your branch + manifest with `python -m tools.agent.manifest_helper session-save <label>` and restore them later with `... session-restore <label>`.

## Operating Rhythm
- **Receipts-first** – no step is “done” until receipts exist. Record artifacts under `_report/agent/<id>/…` and cite them in the plan. (Governance anchor: `docs/workflow.md#architecture-gate-before-writing-code`.) Use `--scaffold` on `tools.agent.task_assign`, `tools.agent.claim_seed`, or `tools.planner.cli new` to generate the skeleton on day zero.
- **Install the guard hook once per clone** – run `tools/hooks/install.sh` to wire the repo-managed pre-push hook (it runs receipts check, planner validation, and targeted pytest before every push).
- **Preflight every push** – run `tools/agent/preflight.sh` before pushing or requesting review; it mirrors the hook (receipts, plan guard, planner validate, bus status, targeted pytest) and enforces the manager directive in `_bus/messages/manager-report.jsonl`.
- **Stay on the bus** – log progress with `python3 -m tools.agent.bus_event log --event status …` and monitor peers via `docs/parallel-codex.md#self-audit` (`python -m tools.agent.bus_status --preset support --agent <id>` for quick snapshots).
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
