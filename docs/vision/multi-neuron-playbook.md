# Multi-Neuron Playbook — 2025-09-23

Guidance for onboarding new humans/LLMs (“neurons”) into TEOF’s organism while
respecting L0–L3 guardrails and maintaining cooperative cadence (O6).

## Roles
- **Operator (You):** steward of L0/L1, curates reflections, resolves conflicts,
  and sets consent policy.
- **Codex Neuron:** enforces guardrails, interprets prompts, emits receipts.
- **Guest Neuron (Human/LLM):** consumes conductor prompts, proposes actions,
  logs receipts, respects diff/test caps.

## Onboarding Checklist
1. Review `docs/vision/objectives-ledger.md` and `docs/vision/properties-ledger.md`.
2. Acknowledge consent policy in `docs/automation/autonomy-consent.json`.
3. Register identity in `_bus/claims/` or via `tools.agent.session_boot`.
4. Run `teof-objectives-status --window-days 7` to understand current cadence.
5. Pick a backlog item (`_plans/next-development.todo.json`) and claim via
   conductor (`teof-conductor --plan-id ND-### --watch --dry-run`).

## Engagement Rhythm
- **Daily:** review new reflections (`memory/reflections/`), log your own via
  `teof-reflection-intake`.
- **Weekly:** run `teof-objectives-status`, update backlog statuses, and ensure
  O1/O2/O5/O7 targets are met.
- **Pilot cycles:** when integrating automation, capture metabolite receipts,
  reflection summaries, and guardrail compliance (P1–P6).

## Exit / Pause
- Toggle `auto_enabled` in `docs/automation/autonomy-consent.json` to halt unattended
  runs.
- Log a final reflection summarising outstanding work and point to receipts.
