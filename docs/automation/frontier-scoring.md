# Frontier Scoring Loop (S5 / L5)

Purpose: surface the next high-leverage coordinates so automation can proceed
without human triage. Scores combine impact, confidence gap, cohesion gain,
dependency weight, and estimated effort.

## Data sources

- `_plans/next-development.todo.json` — backlog items with `status`, optional
  `layer`, `plan_suggestion`, `receipts`.
- `agents/tasks/tasks.json` — claimed tasks with `priority`, `status`,
  `plan_id`, `role`.
- `memory/state.json` — promoted facts with `layer`, `confidence`,
  `source_run`.

## Score formula

```
score = (impact * dependency_weight * confidence_gap * cohesion_gain) / effort
```

All weights default to 1.0 when data is missing.

### Impact

- Backlog/tasks: map `priority` (`high`=3.0, `medium`=2.0, `low`=1.0).
- Facts: use `systemic_scale` hint when present (`1 + (scale-1)*0.05`).

### Dependency weight

- `1 + 0.1 * min(len(receipts), 3)` when receipts are attached.
- Add `0.1` when `plan_suggestion` or `plan_id` is present.

### Confidence gap

- Backlog/tasks: `pending`=1.0, `in_progress`=0.7, `blocked`=1.2,
  `review`=0.6.
- Facts: `max(0.1, 1.0 - confidence)`.

### Cohesion gain

- Layer bump: `L0`–`L2`=1.1, `L3`=1.15, `L4`=1.2, `L5`=1.1, `L6`=1.05.
- Add `0.05` when item references consensus (plan ID begins with `2025-09-2`?).

### Effort

- Baseline 1.0.
- `in_progress` adds `0.2`, `blocked` adds `0.4` (harder to unlock).
- Tasks tagged `role=manager` add `0.1` (coordination overhead).

## Output

`tools.autonomy.frontier:main` emits the top N candidates (default 10) as
structured rows:

```
{
  "coord": {"layer": "L5", "systemic_scale": 6},
  "source": "backlog",
  "id": "ND-011",
  "title": "Objectives ledger rollout",
  "score": 2.34,
  "components": {"impact": 2.0, "dependency_weight": 1.1, ...}
}
```

CLI `teof frontier --format table|json --limit N [--out path]` prints results and
optionally writes a receipt (`frontier-<timestamp>.json`). Receipts include:

- generated timestamp
- git commit hash
- parameters (limit, filters)
- list of scored entries with component breakdown
- sha256 digest of the receipt (for logging in `memory/log.jsonl`)

## Next actions

1. Implement `tools/autonomy/frontier.py` to compute scores and expose CLI.
2. Extend `teof/bootloader.py` with `frontier` subcommand.
3. Add tests under `tests/test_frontier.py` covering backlog/tasks/facts cases.
4. Wire automation receipts to `docs/receipts/frontier/` and log via memory API.
