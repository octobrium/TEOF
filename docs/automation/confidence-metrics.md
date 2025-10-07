# Confidence Metrics (Agent Self-Calibration)

This note sketches a lightweight schema for agents to record their perceived
confidence before taking actions. The intent is to surface overconfidence early
so stewards can inspect receipts and adjust guardrails.

## Schema

Confidence reports append to `_report/agent/<agent-id>/confidence.jsonl` using
this shape:

```json
{
  "ts": "2025-10-06T20:35:00Z",
  "agent": "codex-4",
  "confidence": 0.72,
  "note": "OCERS scan expected to pass"
}
```

- `ts`: ISO-8601 UTC timestamp when the report was captured.
- `agent`: Agent identifier.
- `confidence`: Float in `[0.0, 1.0]` representing subjective probability of
  success (0 = no confidence, 1 = certain).
- `note`: Optional free-form string with context (task, plan, or command).

## Usage

The `session_boot` helper accepts `--confidence` and `--confidence-note`
arguments. When provided, the report is appended automatically as part of the
session receipts. Agents may also log additional entries manually if confidence
shifts during a session.

Run `python -m tools.agent.confidence_report --agent <id>` to summarise logged
entries. Pass `--warn-threshold` to highlight repeated high-confidence entries
and `--format json` for machine-readable output.

## Next Steps

- Aggregate confidence vs. outcome data into dashboards (`confidence_report`
  provides basic counts and warnings).
- Alert when high-confidence predictions fail repeatedly (overconfidence).
- Incorporate into manager reports or autonomy guards.
