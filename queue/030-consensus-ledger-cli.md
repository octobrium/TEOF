# Task: Ship consensus ledger CLI
Goal: provide `python -m tools.consensus.ledger` to render current agent votes, anchors, and receipts for ledger-backed decisions.
Notes: include filters for decision id, agent, and timeframe; output JSONL + table formats.
Coordinate: S6:L5
Systemic Targets: S1 Unity, S2 Energy, S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: revisit after consensus automation stabilizes.
Fallback: manual parsing of `_bus/events/events.jsonl` and governance ledger entries.
