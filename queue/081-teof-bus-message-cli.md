# Task: Add teof bus_message CLI
Goal: expose `tools.agent.bus_message` via the teof command so coordination updates share the same entrypoint as bus_status/watch/event.
Notes: reuse parser logic, ensure claim guard behavior stays intact, update docs/tests, and mention `--target` support in the new alias instructions.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: once CLI + docs/tests land.
Fallback: continue calling `python -m tools.agent.bus_message`.
