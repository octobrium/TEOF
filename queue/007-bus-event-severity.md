# Task: Add severity tagging to bus_event
Goal: let agents classify coordination events as low/medium/high severity for downstream tooling.
Notes: extend CLI to accept `--severity`, validate values, persist in JSON payload, and document usage.
OCERS Target: Coherence↑ Evidence↑ Safety↑
Coordinate: S3:L5
Sunset: revisit once severity rolls into unified analytics.
Fallback: keep emitting severity notes via --extra.
