# Task: Add teof macro_hygiene CLI
Goal: let operators run the macro hygiene ledger check via `python3 -m teof macro_hygiene ...` instead of the internal module path.
Notes: reuse tools.autonomy.macro_hygiene parser, wire into teof command registry, add tests/docs.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: once CLI + docs/tests land.
Fallback: keep using `python -m tools.autonomy.macro_hygiene`.
