# Autonomy Audit Digest (L6 → L5)

**Status:** Draft (2025-10-20T08:40Z)  
**Owner:** codex (plan `2025-10-20-autonomy-audit-aggregation`)

## Intent

Collapse the high-frequency autonomy audit receipts under
`_report/usage/autonomy-audit/` into a rolling digest so that:

- Observability remains intact (layers/gaps stay queryable).
- Git history and CI stop churning on hundreds of single-run receipts.
- Older audit details remain recoverable via append-only archive (`_report/usage/autonomy-audit/archive/`).

## Digest contract

The aggregation command emits `_report/usage/autonomy-audit/summary-latest.json`
with the following schema:

```jsonc
{
  "generated_at": "UTC timestamp",
  "window": {
    "start": "first-run timestamp in window",
    "end": "last-run timestamp in window"
  },
  "source": "_report/usage/autonomy-audit",
  "total_runs": 123,                    // number of receipts processed
  "layers_seen": {                      // counts across all runs
    "connectivity": 42,
    "backfill": 37
  },
  "gaps_seen": {
    "connectivity": 39,
    "recursive-integrity": 12
  },
  "latest_runs": [                      // most recent k runs (default 5)
    {
      "generated_at": "...",
      "layers": ["backfill", "connectivity"],
      "gaps": ["connectivity"]
    }
  ],
  "retained": [                         // filenames left in place
    "audit-2025-10-20T07:01:00Z.json",
    "audit-2025-10-20T07:16:00Z.json"
  ],
  "archived": {
    "stamp": "20251020T084000Z",
    "count": 317,
    "destination": "_report/usage/autonomy-audit/archive/20251020T084000Z/",
    "manifest": "_report/usage/autonomy-audit/archive/20251020T084000Z/manifest.json"
  }
}
```

### Parameters

- `--retain N` keeps the most recent `N` fine-grained receipts alongside the digest (default 5).
- `--no-archive` skips moves into the archive directory (useful for dry runs).
- `--digest PATH` overrides the summary output (defaults to `summary-latest.json`).
- `--window DAYS` restricts aggregation to the last *DAYS* (others archive immediately).

## Retention rules

1. Latest *N* runs remain in `_report/usage/autonomy-audit/` for debugging.
2. Older receipts move to `_report/usage/autonomy-audit/archive/<stamp>/…` preserving filenames and produce a `manifest.json` receipt for that batch.
3. Each digestion captures a receipt (summary + manifest) so automation can reference the run.
4. The digest includes `archived.count` and destination to prove reversibility.

## Guardrails

- Planner/CI hooks must tolerate the new summary file and absence of bulk receipts.
- Tests cover: aggregation stats, archiving behaviour, and `--retain/--no-archive` options.
- A follow-up backlog item updates automation loops (`tools/autonomy/*`) to call the digest command on cadence.

## Next actions

- Implement CLI in `tools.autonomy.autonomy_audit_digest`.
- Write regression tests (`tests/test_autonomy_audit_digest.py`).
- Run the tool once to seed `summary-latest.json` and archive historical receipts.
- Update docs/automation.md and backlog receipts after landing.
