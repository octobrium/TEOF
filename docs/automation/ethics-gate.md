# L6 Ethics Gate (S8 / Automation Guard)

Purpose: block unattended automation from acting on high-risk coordinates
until provenance (consent, human review, safeguards) is present.

## Policy (v0)

- A backlog item or task is considered **high-risk** when either:
  - `systemic_scale >= 8`, or
  - `layer` is `L6`, or
  - `risk` field equals `"high"` (case-insensitive).
- High-risk items must reference at least one receipt whose path contains one
  of the guard keywords: `consent`, `review`, or `ethics`.
- If the guard keyword is missing, the gate raises a violation and the
  automation loop should refuse to execute until receipts are attached.

### Coherence vs. Ethics

- Coherence guards (frontier, critic, TMS) answer “does the plan make structural sense?”
- The ethics gate answers “should this plan be allowed to act with the current receipts?”
- A task can be coherent yet still violate ethics if provenance is missing. Treat missing receipts as an ethics defect, not a coherence bug, and escalate through this gate before automation proceeds.
- Before escalating, confirm higher systemic axes (Unity → Power) remain satisfied or actively defended (see [`docs/foundation/systemic-scale.md#hierarchy-enforcement`](../foundation/systemic-scale.md#hierarchy-enforcement)). Ethics does not outrank Resilience/Truth; it inherits them.

Receipts produced by this gate live under `docs/receipts/ethics/`:

```
{
  "generated_at": "2025-09-26T21:45:00Z",
  "git_commit": "e803f21",
  "violations": [
    {
      "id": "ND-014",
      "title": "Relay offering pilot",
      "coord": {"layer": "L6", "systemic_scale": 8},
      "reason": "missing_guard_receipt",
      "required_keywords": ["consent", "review", "ethics"],
      "receipts": []
    }
  ]
}
```

## CLI usage

```
teof ethics --out docs/receipts/ethics/<UTC>/ethics.json [--emit-bus]
```

- Prints a summary of violations; `--format json` outputs raw JSON.
- When `--emit-bus` is provided, the gate writes claim skeletons to
  `_bus/claims/ETHICS-<id>.json` so manual review can be scheduled.
- Automation should invoke this gate before running L6 actions; if violations
  exist, stop and address them.
- When frontier/critic/TMS highlight missing receipts, funnel the follow-up
  through this gate so the ethics escalation is explicit and auditable.

Future work: integrate with autonomy conductor to enforce guardrails inline
and attach additional risk metadata.
