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
  "note": "legacy loop scan expected to pass"
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

## Calibration pipeline

Run the end-to-end CLI to collect, aggregate, and alert on calibration drift:

```bash
# 1) Collect raw entries from _report/agent/*/confidence.jsonl
python -m tools.agent.confidence_calibration collect \
  --out artifacts/confidence_calibration/latest.json

# 2) Aggregate against plan outcomes + emit receipts
python -m tools.agent.confidence_calibration aggregate \
  --source artifacts/confidence_calibration/latest.json \
  --report-dir _report/usage/confidence-calibration

# 3) Evaluate alerts and (optionally) emit bus events
python -m tools.agent.confidence_calibration alerts \
  --summary _report/usage/confidence-calibration/summary-<ts>.json \
  --emit-bus
```

- `collect` scans every agent confidence log and attempts to infer the plan id
  from embedded metadata (`plan:2025-11-09-example`). Entries are stored in a
  normalized artifact so downstream steps operate deterministically.
- `aggregate` joins the collected entries with `_plans/*.plan.json` statuses to
  compute mean delta, mean absolute delta, Brier score, and over/underconfidence
  rates. Receipts land in `_report/usage/confidence-calibration/summary-*.json`
  plus a markdown dashboard for manager-report attachments.
- `alerts` reads a summary, evaluates thresholds (defaults: `|mean_delta|>0.15`
  or overconfidence rate `>0.30`), writes `_report/usage/confidence-calibration/alerts-*.json`,
  and can emit a `confidence-alert` bus event.

CI/automation can now gate merges by running the aggregate + alerts steps and
failing when alerts fire.

## Dashboards & Alerts

Run the watcher to scan every `_report/agent/<id>/confidence.jsonl` file and
highlight potential overconfidence:

```bash
python -m tools.agent.confidence_watch --format table --report-dir _report/usage/confidence-watch
```

- `--warn-threshold` (default `0.9`) marks entries to count as "high"
- `--window` (default `10`) focuses the check on the most recent entries; pass
  `0` to evaluate the full log
- `--alert-ratio` (default `0.6`) and `--min-count` (default `5`) determine when
  an agent is flagged. Alerts also return a non-zero exit code when
  `--fail-on-alert` is provided.

JSON snapshots land in `_report/usage/confidence-watch/confidence-watch-<ts>.json`
so stewards can compare runs. Use `--format json` for machine-readable output.

`python -m tools.agent.batch_refinement` runs the watcher automatically and fails
the batch when alerts fire (unless `--allow-confidence-alerts` is provided). This
keeps overconfidence escalations inline with the systemic Truth → Ethics contract
before automation publishes heartbeats.

## Next Steps

- Correlate confidence reports with task outcomes to measure calibration drift.
- Surface alerts automatically in manager reports or autonomy guards once the
  watcher is battle-tested.
