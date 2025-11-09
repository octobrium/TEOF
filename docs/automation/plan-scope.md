# Plan Scope Automation

When multiple agents work in the same repository, pushes must stay scoped to a single plan so receipts, bus traffic, and reviews stay coherent. `teof plan_scope` helps by deriving the file set that belongs to a plan (plan JSON + receipts + related task coordination files) and optionally writing a manifest for reuse.

## Usage

List the files tied to a plan:

```bash
python3 -m teof plan_scope --plan 2025-11-09-plan-scope
```

Output columns:

- `path` – repository-relative path
- `exists` – whether the file currently exists
- `source` – why the file is included (`plan`, `receipt`, `task_claim`, etc.)

Emit JSON instead of a table:

```bash
python3 -m teof plan_scope --plan 2025-11-09-plan-scope --format json
```

Write a manifest file (useful when creating a temporary worktree or sparse checkout):

```bash
python3 -m teof plan_scope --plan 2025-11-09-plan-scope --manifest _plan_scope/manifests/plan-scope.json
```

The manifest contains the `plan_id`, generation timestamp, and the resolved file list (with existence metadata). You can feed this manifest into custom tooling to create scoped worktrees, sparse checkouts, or push pipelines.

Every invocation logs an observation receipt automatically:

```bash
python3 -m teof plan_scope --plan 2025-11-09-plan-scope --manifest _plan_scope/manifests/plan-scope.json
```

Receipts land in `_report/usage/plan-scope/plan-scope-<slug>-<ts>.json`, and `_report/usage/plan-scope/latest.json` is updated with a pointer to the most recent run. Pass `--receipt-dir <path>` to redirect receipts (defaults to `_report/usage/plan-scope`) or `--no-receipt` only when a test already tracks its own receipts.

## Recommended Workflow

1. Before starting implementation work, run `teof plan_scope --plan <id>` to sanity-check the files tied to your plan.
2. When you're ready to push, create a clean worktree (e.g., via `git worktree add`) and copy or checkout only the files from the manifest. This keeps preflight under the change-limit guardrail.
3. Run `tools/agent/preflight.sh full` inside the scoped worktree, log receipts, and push.
4. Delete the scoped worktree or reuse it for the next plan.

This approach keeps each push auditable and prevents large, multi-plan diffs from tripping the preflight guard. When juggling multiple plans, run `teof deadlock --format json` and archive the output under `_report/deadlock/` so coordination logs capture the state before any escape-valve protocol kicks in.
