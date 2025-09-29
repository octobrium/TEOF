# Task: Automate consensus receipt logging
Goal: add tooling so when consensus decisions close, receipts are auto-appended under `_report/consensus/` and linked to bus events.
Notes: integrate with `tools/agent/bus_event` or a helper CLI; ensure CI validates receipt presence.
OCERS Target: Ethics↑ Reproducibility↑
Coordinate: S6:L5
Sunset: retire if consensus flow becomes part of capsule automation.
Fallback: managers append receipts manually via `python tools/receipts/main.py`.
