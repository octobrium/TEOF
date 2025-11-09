# Consensus Handoff Protocol

When a seat cannot reach the TEOF bus (sandboxed CLI, offline environment, etc.) but consensus or push approval is required, log a **handoff receipt** so the next available agent can continue without guesswork.

## Workflow

1. Capture the observation in `_report/analysis/...` (free-form or via plan notes).
2. Run:
   ```bash
   python -m tools.automation.consensus_handoff \
     --pending-action "Push feature/awesome" \
     --reason "No bus access from sandbox" \
     --agent-id codex-5 \
     --plan-id 2025-11-09-autonomy-module-consolidation \
     --branch feature/awesome \
     --details "Needs consensus + push" \
     --requires-push
   ```
3. The CLI writes `_report/analysis/consensus-handoff/handoff-<stamp>.json` plus `_report/analysis/consensus-handoff/latest.json`.
4. Share the receipt path with the maintainer (e.g., via manager-report) so another seat can bus-claim, review, and push.

## Receipt fields

| Field | Description |
| --- | --- |
| `generated_at` | UTC timestamp |
| `agent_id` | Seat logging the handoff |
| `pending_action` | What needs consensus/push |
| `reason` | Why the current seat can’t do it |
| `plan_id`, `branch` | Optional references |
| `requires_push` | Set when the next action is pushing to main |
| `next_steps` | Instructions for the next agent |

## Guardrails

- Always include a `plan_id` or `branch` so reviewers know exactly what to inspect.
- Keep receipts under version control (`_report/analysis/consensus-handoff`). CI can later ensure the pointer is fresh if desired.
- Once another agent completes the action, they should reference the receipt in their bus logs/plan steps so the trail stays intact.
