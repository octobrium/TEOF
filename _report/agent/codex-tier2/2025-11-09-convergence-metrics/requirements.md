# ND-071 Convergence Metrics Requirements (2025-11-09T05:36Z)

Sources: queue/071-convergence-metrics.md, docs/reflections/20250917-convergence-metrics.md, tools/network/receipt_sync.py.

Requirements:
1. **Signals** – hash alignment vs upstream, receipt coverage %, anchor latency, commandment adoption rate, plan/claim drift count.
2. **Data taps** – `_report/network/receipt_sync/*.json`, `_report/reconciliation/` outputs, `_bus/events/events.jsonl` for anchor commits.
3. **Storage** – `_report/reconciliation/metrics.jsonl` (append-only) and `_report/usage/convergence-dashboard/summary-<ts>.json` for human dashboards.
4. **CLI** – `python -m tools.network.convergence_metrics collect|aggregate|report --window 24h` similar staging to confidence calibration.
5. **Alerts** – emit bus events when any metric breaches thresholds (e.g., anchor latency > 30m).
6. **Docs/tests** – update reflections doc + add pytest fixture verifying aggregator math.
