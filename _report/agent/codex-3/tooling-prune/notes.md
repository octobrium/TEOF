# Tooling Prune Audit (S1)

## Surface inventory
- `tools/agent/` python entrypoints: `bus_claim.py`, `bus_event.py`, `bus_message.py`, `bus_status.py`, `bus_watch.py`, `claim_seed.py`, `idle_pickup.py`, `manager_report.py`, `manifest_helper.py`, `session_boot.py`, `session_brief.py`, `task_assign.py`, `task_sync.py`. Shell helpers: `preflight.sh`, `runner.sh`.
- Documentation touch points: `docs/agents.md`, `docs/collab-support.md`, `docs/parallel-codex.md`, `docs/workflow.md`, `_bus/README.md`, recent governance/manager plans. Each references the corresponding `python -m tools.agent.*` invocation.
- Related automation beyond `tools/agent`: `tools/maintenance/prune_artifacts.py` (apoptosis workflow), `scripts/ops/apoptosis.sh`, `scripts/ci/guard_*` (guard rails); will cross-check overlap before pruning.

## Flag & UX survey (captured via `--help` output)
- **bus_status**: `--limit`, `--agent`, `--active-only`, `--json`, `--since`, `--manager-window` (new heartbeat guard).
- **bus_watch**: shares `--since`, `--agent`, `--event`, `--follow`, `--limit`; window flag is `--window-hours` (default 24).
- **bus_event log**: requires `--event` + `--summary`; optional `--task`, `--plan`, `--branch`, `--pr`, `--receipt`, consensus flags, `--severity`, `--agent`, `--extra` pairs.
- **bus_message**: `--task`, `--type`, `--summary`, optional `--agent`, `--branch`, `--plan`, `--receipt` (repeatable), `--meta` (repeatable), `--note`.
- **bus_claim**: subcommands `claim` (`--task`, `--plan`, `--agent`, `--branch`, `--status`, `--notes`, `--allow-unassigned`) and `release` (mirrors but enforces existing claim).
- **claim_seed**: mirrors claim creation but defaults status to paused and allows timestamp override.
- **idle_pickup**: `list` & `claim`; currently lacks JSON or filter options noted in docs.
- **manager_report**: single optional `--manager` flag; generates manager summary receipt.
- **manifest_helper**: `list|activate|restore`; docs rely on activate/restore around role swaps.
- **session_boot** / **session_brief**: handshake + context fetch; both documented as part of idle/sync workflows.
- **task_assign**: `--task`, `--engineer`, `--plan`, `--branch`, `--manager`, mutually exclusive `--auto-claim/--no-auto-claim`, `--note`.
- **task_sync**: `--dry-run` toggle.
- Shell helpers: `preflight.sh` (wraps guard scripts) and `runner.sh` (local runner entrypoint).

## Observed drift / candidates for cleanup
- Duplicative domain overlap between `bus_claim` (manual) and `claim_seed`+`task_assign` (managed path). Need rubric on when to prune direct `bus_claim` usage vs. keep for emergency override.
- `idle_pickup` lacks documentation around `--json`/filter behaviour (not implemented) while docs suggest list/claim usage—validate actual needs before extending or pruning.
- `manager_report.py` exists but latest manager updates rely on manual bus messages; confirm whether helper is still used or stale.
- `bus_watch`/`bus_status` share semantics but diverge on `--window-hours` vs `--manager-window`; UX alignment candidate.
- Shell helper `runner.sh` duplicates capabilities of `python -m tools.runner`; determine whether to migrate to unified entrypoint or document scope.

## Next steps for S2–S4
- Map actual usage from `_bus/messages/*.jsonl` and `_bus/events/events.jsonl` to see which helpers still emit receipts (esp. `manager_report`, `runner.sh`).
- Identify helpers without pytest coverage (`idle_pickup`, `manager_report`, potentially `task_sync`).
- Confirm apoptosis targets for stale scripts (e.g., redundant ops scripts) once usage validated.

