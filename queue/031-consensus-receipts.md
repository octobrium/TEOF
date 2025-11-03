# Task: Automate consensus receipt logging
Goal: add tooling so when consensus decisions close, receipts are auto-appended under `_report/consensus/` and linked to bus events.
Notes: integrate with `tools/agent/bus_event` or a helper CLI; ensure CI validates receipt presence.
Coordinate: S6:L5
Systemic Targets: S4 Resilience, S5 Intelligence, S6 Truth, S8 Ethics
Layer Targets: L5 Workflow
Sunset: retire if consensus flow becomes part of capsule automation.
Fallback: managers append receipts manually via `python tools/receipts/main.py`.
