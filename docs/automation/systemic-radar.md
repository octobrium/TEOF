# Systemic Health Radar (Design Draft)

**Status:** Draft specification  
**Owner:** codex-tier2 (2025-11-08)  
**Purpose:** Define the minimum data contract for an automated systemic radar that surfaces S1–S10 (systemic axes) and L0–L6 (layer) coverage using existing receipts before the CLI/CI guard is automated.

## Problem

- `_plans/next-development.todo.json` only describes queue state; it does not reflect macro hygiene, authenticity, or memory cadence.
- `_report/usage/` hosts dozens of receipts (backlog health, macro hygiene, push readiness, autonomy status) but there is no unified snapshot connecting them to systemic axes.
- Steward seats need an auditable “radar” before autonomy batches run so they can pause work whenever an axis or layer drifts.

## Scope (MVP)

| Input | Source | Signal | Axis/Layer |
|-------|--------|--------|-----------|
| Backlog pending count | `_report/usage/backlog-health/*.json` | `pending_threshold_breached`, `pending_items` | S3 Propagation / L5 |
| Macro hygiene objectives | `_report/usage/macro-hygiene-status.json` | `summary.ready/attention`, failing checks | S4 Resilience / L4–L5 |
| Autonomy receipts | `_report/usage/autonomy-status.json` (future) | `autonomy_guard_ready`, `pending_followups` | S2 Energy / L6 |
| Plan receipts coverage | `_plans/*.plan.json` + `_report/planner/validate/summary-*.json` | ratio of done plans with receipts | S6 Truth / L4 |
| Memory cadence | `memory/log.jsonl` | count of entries in trailing 7 days tagged `systemic` | S1 Unity / L0 |

The radar aggregates these signals into `systemic_index` objects, each with:

```json
{
  "axis": "S1",
  "layer": "L0",
  "status": "ready|attention|breach",
  "detail": "...",
  "receipts": ["_report/usage/backlog-health/....json"]
}
```

## Output Contract

- Receipt path: `_report/usage/systemic-radar/systemic-radar-<UTC>.json`
- Symlink `_report/usage/systemic-radar/latest.json`
- JSON payload:

```json
{
  "generated_at": "2025-11-08T21:50:00Z",
  "version": 0,
  "axes": [
    {
      "axis": "S1",
      "layer": "L0",
      "status": "ready",
      "detail": "memory/log.jsonl has 12 systemic entries in trailing 7d (target >= 5)",
      "receipts": ["memory/log.jsonl#2025-11-08T21:40:00Z"],
      "metric": 12,
      "threshold": 5
    }
  ],
  "summary": {
    "ready": 3,
    "attention": 1,
    "breach": 1
  }
}
```

## Implementation Notes

1. `python -m tools.autonomy.systemic_radar` (new module) will:
   - Load backlog health receipts (latest) to compute S3 status.
   - Load macro hygiene status to compute S4.
   - Parse `_plans/*.plan.json` to compute the receipts-per-plan ratio.
   - Inspect `memory/log.jsonl` for systemic-tagged entries in trailing 7 days.
   - Read `docs/automation/systemic-radar.baseline.json` for axis thresholds (target values, receipt sources, freshness windows).
2. CLI flags:
   - `--output` to override receipt path.
   - `--memory-window-days` to tune trailing window (defaults to baseline config values).
   - `--baseline-config` to point at an alternate JSON config (default: `docs/automation/systemic-radar.baseline.json`).
3. Every run writes receipts + optional Markdown summary for `docs/reports/systemic-radar.md`.

## Next Steps

1. **(DONE)** Build baseline config file enumerating each axis metric and acceptable thresholds.
2. **(DONE)** Implement the `tools.autonomy.systemic_radar` module to emit receipts per contract.
3. Add CI guard (`scripts/ci/check_systemic_radar.py`) to ensure the latest receipt is under 24h old before autonomy loops execute.
4. Publish dashboards (`docs/reports/systemic-radar.md`) summarizing the latest receipt so stewards can scan status without re-running the CLI.
5. Wire CI guard (`scripts/ci/check_systemic_radar.py`) into autonomy workflows so stale receipts block promotion.
