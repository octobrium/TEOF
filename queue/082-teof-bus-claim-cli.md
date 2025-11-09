# Task: Add teof bus_claim CLI
Goal: expose claim management via `python -m teof bus_claim ...` so all coordination helpers share the same entrypoint.
Notes: share parser/run helpers with tools.agent.bus_claim, add regression tests (claim + release flows), and update docs referencing bus_claim usage.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: once CLI + docs/tests land.
Fallback: continue using `python -m tools.agent.bus_claim`.
