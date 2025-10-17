# Autonomy Preflight Module

`python3 -m tools.autonomy.preflight` aggregates the checks that gate autonomy
runs:

- Authenticity snapshot (`_report/usage/external-authenticity.json`).
- Planner status (`_report/planner/validate/summary-latest.json`).
- Objectives status (`tools.autonomy.objectives_status`).
- Frontier preview, critic alerts, TMS conflicts, ethics violations.
- Fractal conformance status (queue/plan/memory retired observation loop + coordinate coverage).

Running the CLI writes a receipt under `_report/usage/autonomy-preflight/`:

```bash
python3 -m tools.autonomy.preflight
```

Use it in CI or scheduled jobs to detect guard failures before executing the
conductor. The conductor now consumes the same snapshot, so both humans and
automation rely on one canonical preflight path.
