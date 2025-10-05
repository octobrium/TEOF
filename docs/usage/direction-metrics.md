<!-- markdownlint-disable MD013 -->
# Direction-of-Travel Metrics (TTΔ Scorecard)

TEOF evaluates direction, not just snapshots. This scorecard turns the legacy TTΔ heuristic (Observation Capacity, Coherence, Recursion Depth, Integrity Gap, Sustainability, Safe Optionality) into measurable signals that already exist in the repo.

Use the table during weekly manager reviews and whenever `_report/usage/manager-report.md` is regenerated. Each metric must be backed by receipts or automated reports stored under `_report/` or `artifacts/`.

Running `python -m tools.agent.manager_report` now appends every TTΔ snapshot to `memory/impact/ttd.jsonl`, giving a ready-made history for plotting or anomaly detection.

| Metric | Definition | Primary Evidence | Target | Recording |
| --- | --- | --- | --- | --- |
| **Observation Capacity (OC)** | Relevant signals captured per cost. | `_report/usage/receipts-latency-latest.jsonl`, `_report/usage/receipts-index-latest.jsonl`, `_bus/events/events.jsonl` heartbeats. | Latency p95 ≤ 5 min, no missing heartbeat > 30 min. | Log summary in manager report (`observation.capacity`). |
| **Coherence Score (CS)** | Accuracy of models vs. receipts/tests. | `pytest` pass rate, `scripts/ci/check_consensus_receipts.py`, `artifacts/consensus/ci-dashboard.txt`. | 100 % CI pass; consensus drift = 0. | Record as `coherence.score`. |
| **Recursion Depth (RD)** | Closed loops from observation → plan → correction. | `_plans/`, `_bus/claims/*.json`, `_report/usage/plan-lint/*.json` and plan hygiene tests. | Every contradiction produces a plan + closure receipt within 48 h. | Track open/closed ratio (`recursion.depth`). |
| **Integrity Gap (IG)** | Delta between stated policy and behaviour. | Guardrails badge, `scripts/policy_checks.sh`, `governance/anchors.json` append-only audit, capsule hash checks. | Zero unresolved failures; capsule/current symlink correct. | Record last failure timestamp (`integrity.gap`). |
| **Sustainability (SC)** | Ability to run under failure/starvation. | Scheduled bus heartbeat (`.github/workflows/bus-heartbeat.yml`), `_report/usage/autonomy-status.json`, quickstart smoke receipts. | Heartbeat succeeds for 7d; quickstart receipts regen ≤ daily. | Capture in manager report (`sustainability.signal`). |
| **Safe Optionality (SO)** | Option sets preserved for peers. | Mirror status (cold storage ledger), `governance/anchors.json` key registry, `docs/badges/`, `_report/usage/external-authenticity.md`. | ≥2 signed mirrors current; authenticity ≥0.7. | Record as `optional.safe`. |

> **Reminder:** verbal commitments (“next time”, “mental note”, etc.) without receipts count as IG debt. Use `python -m tools.autonomy.commitment_guard` to surface unbacked statements and file a plan before concluding the session.

### Operating Cadence

1. **Collect signals** – Run `python -m tools.agent.manager_report` (or your preferred manager script) to refresh `_report/usage/manager-report.md`.
2. **Update dashboard** – Append the six scalar values to the weekly section in `manager-report`. Include links into `artifacts/` or `_report/usage/` for evidence.
3. **Trend tracking** – Optionally export the set into `memory/impact/ttd.jsonl` (append-only) for historical plots.
4. **Escalation rule** – Any metric below target triggers a plan with OCERS vector ≥ Coherence and a bus broadcast describing the gap.

### Relationship to OCERS

- **Observation** → OC, IG
- **Coherence** → CS, RD
- **Ethics** → IG, SO
- **Reproducibility** → CS, SC
- **Self-repair** → RD, SC

When all six metrics trend up while IG trends down, TTΔ is positive and the system is aligned with the North Star (expanding observation, reducing incoherence, preserving options).

---

**References**
- Legacy summary: `Infodumps/meat infodump 3.txt` (TTΔ guidance)
- Current automation: `.github/workflows/guardrails.yml`, `.github/workflows/bus-heartbeat.yml`
- Receipts indices: `_report/usage/receipts-*.jsonl`
