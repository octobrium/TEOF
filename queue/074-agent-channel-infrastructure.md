# Task: Agent Channel Infrastructure
Goal: implement role-based agent inbox channels so agents can send targeted feedback without leaving manager-report.
Notes: add `--target` support to `bus_message`, ship a `bus_inbox` reader, have `session_boot` surface inbox health, and document workflow per the 2025-11-09 design + decision records (`_report/assessments/20251109-agent-communication-design.md`, `_report/assessments/20251109-agent-communication-decision.md`).
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: once tooling + docs + receipts cover the agent inbox loop.
Fallback: continue using manager-report broadcasts only (no targeted channel).
