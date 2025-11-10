# TEOF Planner Scaffold

Purpose: codify session/workstream plans as deterministic artifacts that feed CI evaluation.

- Plans live in `_plans/` using JSON (`*.plan.json`).
- Each plan captures author, intent, ordered steps with statuses, and the next checkpoint to verify.
- Receipts from automated evaluation (e.g., `tools/runner`) are referenced for provenance.

## File format (v0)

```
{
  "version": 0,
  "plan_id": "2025-09-17-planner-scaffold",
  "created": "2025-09-17T06:00:00Z",
  "actor": "codex",
  "summary": "Bootstrap planner + eval scaffolding",
  "status": "queued",
  "steps": [
    { "id": "S1", "title": "Create scaffolding", "status": "queued", "notes": "README + sample plan", "receipts": [] }
  ],
  "checkpoint": {
    "description": "Plan validation + minimal eval guard runs in CI",
    "owner": "codex",
    "status": "pending"
  },
  "receipts": ["_report/runner/20250917T060000Z-abcdef.json"],
  "links": [{ "type": "memory", "ref": "PR-28" }]
}
```

### Field requirements
- `version`: integer schema version (start at 0).
- `plan_id`: unique slug (`YYYY-MM-DD-<topic>`); file must be named `<plan_id>.plan.json`.
- `created`: ISO8601 UTC timestamp (Z-suffixed).
- `actor`: matches `git config user.name` or agent handle.
- `summary`: one-line intent.
- `status`: lifecycle (`queued|in_progress|blocked|done`).
- `steps`: ordered list with unique `id` values; each step includes `id`, `title`, `status` (`queued|in_progress|blocked|done`), optional `notes`, and `receipts` (list of receipt paths/URLs). Only one step may be `in_progress` at a time.
- `checkpoint`: object with `description` (non-empty), `owner`, and `status` (`pending|satisfied|superseded`).
- `receipts`: optional list of receipt paths/URLs produced by evaluations. Paths are relative to the repo root, must not escape via `..`, and must exist. Most receipts must be tracked by git, but paths under `_report/` are exempt so automation can capture run artifacts without polluting history. Strict validation enforces both existence and the tracking rule.
- `links`: optional structured references (`type`, `ref`).
- `evidence_scope`: required for `version >= 1`. Object with:
  - `internal`: references to existing TEOF artifacts (docs, memory, receipts) that motivate the plan.
  - `external`: references to literature, datasets, or field evidence outside the repo.
  - `comparative`: optional trend or benchmarking sources (e.g., scaling curves, other frameworks).
  - `receipts`: list of files (e.g., `_report/agent/<id>/<plan_id>/evidence.json`) that capture the actual survey. Non `_report/` paths must be tracked by git; `_report/…` evidence can remain untracked.
  Plans may stay `queued` without receipts while the survey is in progress, but receipts become mandatory before advancing to `in_progress` and automation guards can enforce them via `--require-evidence-plan`.
  See [`docs/reference/evidence-scope.md`](../docs/reference/evidence-scope.md) for detailed guidance and examples.

## Authoring helpers
- `python -m tools.planner.cli new <slug> --summary "..."` scaffolds a plan with lifecycle status `queued` and steps seeded from `--step ID:Title` (defaults to a single `S1`). Optional flags:
  - `--actor/--owner` override the actor and checkpoint owner (default: `git config user.name`).
  - `--checkpoint` customises the initial verification description.
  - `--plan-dir` controls output location, `--timestamp` fixes the `created` field for deterministic tests, and `--force` overwrites existing files.
- Agents may copy `_plans/1970-01-01-agent-template.plan.json` as a starting point when proposing micro tasks; update `plan_id`, `created`, and `actor` before committing.
- `python -m tools.planner.cli status <plan.json> <queued|in_progress|blocked|done>` updates the plan lifecycle, enforcing monotonic transitions (`done` is terminal).
- `python -m tools.planner.cli step add <plan.json> --desc "…" [--id S4] [--note "…"]` appends a queued step (auto-assigns the next `S#` when `--id` is omitted).
- `python -m tools.planner.cli step set <plan.json> <step_id> --status <…> [--note "…"]` advances a step. Re-opening `done` steps or reverting to `queued` is rejected.
- `python -m tools.planner.cli attach-receipt <plan.json> <step_id> --file _report/.../receipt.json` records the receipt under the step and plan, updating the receipt JSON to include `plan_id` + `plan_step_id`.
- `python -m tools.planner.link_memory <plan.json>` appends a provenance entry to `memory/log.jsonl`, bundling the plan artifact and latest receipts.
- `python -m tools.planner.cli show <plan>` prints a summary (status, steps, receipts). Add `--strict` to enforce strict validation before output.
- Use `_plans/agent-proposal-justification.md` as a Markdown pattern when writing proposal evidence for each plan.
- Add `{ "type": "bus", "ref": "_bus/claims/<task>.json" }` inside `links` to connect plans to active bus claims.

## Plan hygiene
- Allowed status transitions: `queued → in_progress|blocked|done`, `in_progress → blocked|done`, `blocked → in_progress|done`, `done` is terminal. CI (`scripts/ci/check_plans.py`) rejects regressions (e.g., `done → in_progress`).
- Steps flagged `done` should carry at least one receipt; attach paths must resolve inside the repo, parse as UTF-8 JSON, and be tracked in git. CI fails if a receipt is missing, ignored/untracked, not JSON, or duplicated.
- When the plan-level checkpoint reports `satisfied`, the plan must list at least one receipt (enforced by the validator’s strict mode).
- Lint status enums with `python -m tools.maintenance.plan_hygiene`. Add `--apply` to normalize common variants (`in-progress` → `in_progress`, `completed` → `done`, etc.).

## Validation + CI
- `python tools/planner/validate.py` checks structural invariants.
- `python tools/planner/validate.py --strict` adds repository-coupled rules (receipt existence/JSON, unique paths, satisfied checkpoint needs receipts). CI uses strict mode.
- `python tools/planner/eval_minimal.py` drives the minimal test battery via `tools/runner`, emitting receipts under `_report/planner/`.
- GitHub Actions (`scripts/ci/check_plans.py`) fails pull requests when plans are invalid, receipts are missing/malformed, or lifecycle regressions occur. `_report/planner/` receipts are uploaded from a non-blocking job for audit.

## Relationship to existing scaffolds
- **PR-28** established the append-only memory log (`memory/log.jsonl`).
- **PR-29** added the hot index for rapid querying of that memory log.
- **PR-30** introduced runner receipts for auditable command execution.

Planner artifacts lean on those primitives: every plan should reference at least one memory entry and attach receipts after evaluations land.

## Lifecycle
1. Open a plan before substantive work (use the CLI scaffold).
2. Update `steps[*]` as work progresses; attach receipts when evaluations land.
3. Run `tools/planner/link_memory.py` once receipts are attached to surface provenance.
4. Mark `checkpoint.status` once the verification step is complete and advance the plan status to `done`.
