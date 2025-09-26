# Truth Maintenance Loop (S6 / L4)

Purpose: detect contradictions inside `memory/state.json` so the system can
open resolution plans and keep facts trustworthy.

## Scope (v0)

- Facts are keyed by `id`. When multiple entries share the same `id` and have
  different statements, layers, or evidence, they are flagged as conflicts.
- Facts with confidence `< 0.4` are treated as unstable and also flagged so the
  next resolution loop can demote or refresh them.

## Receipt format

Receipts live under `docs/receipts/tms/` and include:

```
{
  "generated_at": "2025-09-26T21:20:00Z",
  "git_commit": "6d8a160",
  "state_snapshot": {"log_entries": 53, "facts": 12},
  "conflicts": [
    {
      "id": "memory-schema",
      "statements": ["v0 defined", "v1 pending"],
      "layer": "L4",
      "coord": {"layer": "L4", "systemic_scale": 6},
      "facts": ["fact@20250923T190000Z", "fact@20250926T210000Z"],
      "suggested_plan": {
        "plan_id": "TMS-memory-schema",
        "summary": "Resolve competing memory schema statements",
        "layer": "L4",
        "systemic_scale": 6
      }
    }
  ]
}
```

Plans created from a conflict can be staged under `_plans/` using the suggested
id so other automation can pick them up.

## CLI usage

```
teof tms --out docs/receipts/tms/<UTC>/tms.json
```

- Prints conflicts as a table by default; `--format json` dumps raw payloads.
- When `--emit-plan` is supplied, a lightweight plan skeleton is written to
  `_plans/TMS-<id>.plan.json` so the resolution work can be triaged.

Future iterations will add justification tracking (`justifications:[run_ids]`)
and automatic demotion of stale facts when conflicting evidence wins review.
