# Task: Add severity tagging to bus_event
Goal: let agents classify coordination events as low/medium/high severity for downstream tooling.
Notes: extend CLI to accept `--severity`, validate values, persist in JSON payload, and document usage.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S4 Resilience, S6 Truth
Layer Targets: L5 Workflow
Sunset: revisit once severity rolls into unified analytics.
Fallback: keep emitting severity notes via --extra.
