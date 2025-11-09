# Task: Add teof bus_watch CLI
Goal: allow agents to run `python3 -m teof bus_watch ...` instead of the internal module path, keeping usage aligned with bus_status/inbox.
Notes: share parser logic with tools.agent.bus_watch, support follow mode, document new command alongside bus_status, and add regression tests.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: once CLI wrapper + docs/tests land.
Fallback: continue calling `python -m tools.agent.bus_watch`.
