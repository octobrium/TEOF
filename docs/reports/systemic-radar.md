# Systemic Radar Summary

**Updated:** 2025-11-08T21:56Z  
**Purpose:** Quick human-readable snapshot of the latest systemic radar receipt under `_report/usage/systemic-radar/`.

## Latest Receipt

- File: `_report/usage/systemic-radar/systemic-radar-20251108T215621Z.json`
- Summary: `ready=3`, `attention=1`, `breach=1`
- Breach detail: `S3/L5` (backlog pending below threshold); replenish `_plans/next-development.todo.json` before running autonomy loops.

## How to Refresh

```bash
python3 -m tools.autonomy.systemic_radar
python3 scripts/ci/check_systemic_radar.py  # fails if receipt >24h old
```

Publish the refreshed JSON and update this file’s summary lines so stewards can scan status without re-running the CLI.
