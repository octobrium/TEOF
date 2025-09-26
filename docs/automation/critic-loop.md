# Critic Loop (S4 / L6)

Purpose: detect anomalies that require attention before automation proceeds.
This loop reviews backlog items, active tasks, and memory facts, then surfaces
repair tasks when guardrails detect missing provenance or declining confidence.

## Current heuristics (v0)

1. **Missing receipts (Backlog)**
   - Any backlog item with `status` in {`pending`, `blocked`} and no receipts
     triggers `missing_receipts`.
   - Suggested task: `repair:<item_id>-receipts` (L5).

2. **Low-confidence facts (Memory)**
   - Facts in `memory/state.json` with `confidence < 0.5` trigger
     `low_confidence_fact`.
   - Suggested task: `repair:fact-<id>-confidence` (layer from fact metadata).

Receipts live under `docs/receipts/critic/` with structure:

```
{
  "generated_at": "2025-09-26T21:00:00Z",
  "git_commit": "a1b2c3d",
  "anomalies": [
    {
      "type": "missing_receipts",
      "id": "ND-011",
      "coord": {"layer": "L5", "systemic_scale": 6},
      "details": {"status": "pending"},
      "suggested_task": {
        "task_id": "REPAIR-ND-011",
        "layer": "L5",
        "systemic_scale": 6,
        "summary": "Add receipts for ND-011 backlog item"
      }
    }
  ],
  "state_snapshot": {"log_entries": 53, "facts": 12}
}
```

When run with `--emit-bus`, the critic emits claim files under `_bus/claims/`
for each suggested repair, referencing the anomaly receipt for provenance.

## CLI usage

```
teof critic --out docs/receipts/critic/<UTC>/critic.json [--emit-bus]
```

Outputs a summary table or JSON (use `--format json`) and optionally writes
repair tasks into the bus. Receipts are logged via `memory/log_entry` during
operator workflows.

Future iterations will add:
- Watchers on external authenticity, capsule cadence, and CI summary receipts.
- Contradiction detection tied into the Truth Maintenance System.
- Policy checks for high-risk coords before automation executes.
