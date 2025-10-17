# Ideas Lifecycle

TEOF tracks lightweight research or incubation concepts under `docs/ideas/`. Each idea is a Markdown file with TOML frontmatter so automation can list, triage, and promote it into the formal planner.

## File scaffold

Every idea file starts with a `+++` block describing metadata:

```
+++
id = "decentralized-teof-node"
title = "Decentralized TEOF Node"
status = "draft"
layers = ["L2", "L3", "L4"]
systemic = [2, 4]
created = "2024-10-05T15:00:00Z"
updated = "2024-10-05T15:00:00Z"
+++
# Title
...
```

### Required fields
- `id`: stable slug (matches file stem by default).
- `title`: human readable label (falls back to first Markdown heading).
- `status`: lifecycle stage (`draft`, `triage`, `in_review`, `in_progress`, `promoted`, `archived`).
- `created`: ISO8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`). Automatically populated on first write.
- `updated`: maintained automatically when the CLI rewrites the file.

### Optional fields
- `layers`: list of targeted layers (e.g. `["L4", "L5"]`).
- `systemic`: list of systemic bands addressed (1–10).
- `plan_id`: linked planner artifact once promoted.
- `notes`: free-form rationale snippets, stored as an array.
- `links`: related receipts, plans, or bus claims.

## Workflow
1. **Draft** — capture the idea quickly in `docs/ideas/` (frontmatter + notes).
2. **Triage / In review** — coordination reviews significance, sets layer/systemic targets.
3. **In progress** — active incubation with defined next steps.
4. **Promoted** — linked to a formal `_plans/<plan_id>.plan.json` artifact; execution moves into the planner workflow.
5. **Archived** — closed ideas (superseded, rejected, or complete without promotion). Keep the file for provenance.

Use reflections to record personal insights; use idea files for shared, reusable proposals that may graduate into plans.

### Promotion path
- Capture draft idea with `teof ideas mark <slug> --status draft --layer L4 --systemic 4`.
- Once triaged, open the corresponding plan via `python -m tools.planner.cli new ...`.
- Link the plan back to the idea using `teof ideas promote <slug> --plan-id <plan>` (add `--note "why now"` for provenance).
- Attach receipts to the plan; the idea record stays as the append-only origin story.

## CLI guardrails
The repo-local CLI exposes `teof ideas` helpers:

- `teof ideas list [--status <status>] [--format json]` — inventory ideas with optional filters.
- `teof ideas mark <id> --status <status> [--layer L4] [--systemic 5] [--plan-id 2025-...]` — update metadata.
- `teof ideas promote <id> [--plan-id <plan>] [--layer ...] [--systemic ...]` — set status to `promoted` and optionally link to a plan.
- `teof ideas evaluate [--status triage] [--limit 5] [--show-reasons]` — heuristic pre-filter recommending which ideas deserve promotion attention.

All commands update timestamps automatically and enforce the allowed status values. Combine `--layer` and `--systemic` to keep the systemic mapping explicit before escalation into `_plans/`.

## Promotion checklist
Before running `teof ideas promote`:
- Identify the corresponding layer/systemic targets.
- Ensure a human or agent owns the follow-on plan.
- Open a planner artifact (or schedule it) and capture its `plan_id` in the idea metadata.
- Log supporting receipts or reflections that justify the promotion.

Once promoted, continue work under the planner and reference the idea file from justification notes or receipts for provenance.
