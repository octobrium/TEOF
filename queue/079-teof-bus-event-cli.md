# Task: Add teof bus_event CLI
Goal: expose `python -m tools.agent.bus_event log ...` via the `teof` command so agents use consistent entrypoints for messaging/state updates.
Notes: share parser helpers with tools.agent.bus_event, ensure consensus flags still work, write regression tests, and update docs.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: once CLI + docs/tests land.
Fallback: continue calling the module path directly.
