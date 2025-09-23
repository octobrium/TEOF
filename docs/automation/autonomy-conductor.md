# Autonomy Conductor Guardrails

The autonomy conductor issues Codex prompts that drive unattended backlog work.
This note extracts the non-negotiable guardrails from existing policy so
subsequent implementation matches L0–L5 expectations.

## Policy Inputs

- **Consent policy:** `docs/automation/autonomy-consent.json` keeps
  `auto_enabled`, `continuous`, `require_execute`, and `allow_apply` flags. The
  conductor may only loop when `auto_enabled` and `continuous` are `true` and it
  must obey `require_execute`/`allow_apply` for action execution.
- **Backlog prerequisites:** `_plans/next-development.todo.json` encodes
  authenticity minimum trust and CI health requirements that the conductor must
  respect by delegating selection to `tools.autonomy.next_step`.
- **Diff budget:** Callers pass `--diff-limit <lines>`; prompts must state this
  cap verbatim so downstream agents (or humans) know the allowed change scope.
- **Test expectations:** Repeated `--test` arguments define the required test
  commands. The conductor must list them in the prompt exactly as received.
- **Receipts directory:** `--receipts-dir <path>` indicates where any produced
  receipts must land. This is the auditing anchor and has to appear in the
  prompt contract.

## Prompt Contract

Each generated prompt must include:

1. Task identifiers (`id`, `title`, `plan_suggestion`) pulled from the backlog.
2. Human-readable notes from the backlog item.
3. Guardrail summary listing the diff limit, enumerated tests, and receipts
   directory.
4. Response schema instruction: `analysis`, `commands`, `receipts` keys with
   JSON values so the follow-on tooling can parse the output deterministically.

The prompt is the only channel for diff/test constraints, so any optional text
must not dilute or contradict those guardrails.

## Failure Handling

- **No eligible task:** If `next_step.select_next_step` returns `None`, the
  conductor exits without emitting a prompt.
- **Plan mismatch:** When `--plan-id` is provided and the selected backlog item
  differs, the conductor must unwind the claim (reset status to `pending`) and
  stop silently.
- **Dry-run mode:** With `--dry-run`, the conductor still records the prompt
  receipt but then resets the backlog item to `pending` so other agents can
  claim it.
- **Receipt persistence:** Every cycle writes a JSON receipt under
  `_report/usage/autonomy-conductor/`. The receipt stores the guardrails, a
  snapshot of authenticity/CI status, and the exact prompt so auditors can
  reconstruct what was asked and prove prerequisites were satisfied.
- **Execution instructions:** For non-dry runs the conductor must emit a final
  message reminding operators to execute the suggested commands and honour the
  guardrails. No commands are auto-applied at this stage.

## Open Questions for Implementation

- Should the conductor persist additional metadata (e.g., authenticity snapshot
  hash) to prove prerequisites were satisfied when the prompt was generated?
- How should failure states be surfaced on the bus (status event vs. stdout)
  when the conductor cannot claim a task because authenticity or CI guardrails
  fail upstream?

Answering these questions will inform steps S2–S3 of plan
`2025-09-23-autonomy-conductor`.
