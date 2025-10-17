# Task: Document bus_status staleness window
Goal: capture how `--window-hours` is used and ensure defaults are exercised in tests.
Notes: confirm docs cover default/off semantics; add regression coverage that historical events surface when the flag is disabled.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: remove once unified documentation portal exists.
Fallback: rely on inline CLI help.
