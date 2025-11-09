# Task: Add teof bus_status CLI
Goal: expose `tools.agent.bus_status` under the repo-native `teof` command so agents can run `python3 -m teof bus_status ...` instead of remembering the module path.
Notes: mirror existing `teof inbox` wrapper, keep option parity (all original flags), add tests for both JSON + summary output, and refresh docs/quickstart references.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: once CLI + docs/tests land.
Fallback: continue using `python -m tools.agent.bus_status` until every environment upgrades to the `python3 -m teof bus_status` alias.
