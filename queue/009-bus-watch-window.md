# Task: Add --window-hours to bus_watch
Goal: mirror the staleness window in the streaming CLI so agents can follow recent activity.
Notes: reuse the same semantics as bus_status; update docs/tests accordingly.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: revisit once the bus CLI is consolidated.
Fallback: rely on --since filtering with manual timestamps.
