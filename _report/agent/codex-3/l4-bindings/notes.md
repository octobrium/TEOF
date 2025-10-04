# L4 Bindings Survey — 2025-09-18

## Inputs reviewed
- `governance/core/L2 - objectives/objectives.md`
- `governance/core/L3 - properties/properties.md`
- Guard/CI scripts: `scripts/ci/check_plans.py`, `scripts/ci/check_docs.sh`, `scripts/ci/guard_apoptosis.sh`, `scripts/ci/check_queue.py` (absent; n/a), `tools/preflight.sh`.
- Tests: `tests/test_agent_bus_*.py`, `tests/test_ci_check_plans.py`, `tests/test_reconcile_pipeline.py`, `tests/test_usage_logger.py`.

## Candidate binding pairs (rough)
- **L2.1 Maximize Observation** ↔ `tests/test_agent_bus_watch.py`, `tools/agent/bus_watch.py` receipts.
- **L2.2 Coherence with Observation** ↔ `tests/test_agent_bus_status.py`, `scripts/ci/check_plans.py`.
- **L2.3 Preserve Enabling Conditions** ↔ `scripts/ops/apoptosis.sh`, `_apoptosis/` cadence docs.
- **L2.4 Functional Continuity** ↔ `_plans` lifecycle validators (`tests/test_ci_check_plans.py`).
- **L2.5 Legibility to Many Intelligences** ↔ documentation lint + `docs/agents.md` updates (no explicit guard yet).
- **L2.6 Universality & Portability** ↔ policy to stay text-first (needs future hook).
- **L2.7 Self-Seeding** ↔ capsule + quickstart; guard is `docs/quickstart.md` validation (manual).
- **L2.8 Corrigibility & Stewardship** ↔ `tools/agent/session_boot.py` receipts, bus claims ensures control.
- **L2.9 Recursive Improvement** ↔ planner validators; ensure plans + receipts.
- **L2.10 Resilience & Antifragility** ↔ parallel bus tests.
- **L2.11 Bounded Risk & Reversibility** ↔ `scripts/ci/guard_apoptosis.sh`, claims guard.
- **L2.12 Metrics & Outcome Alignment** ↔ `_report` aggregator tests (`tests/test_reconcile_metrics_summary.py`).
- **L2.13 Incentives aligned with truth-seeking** ↔ consensus backlog (upcoming) — placeholder.
- **L2.14 Diversity Without Decoherence** ↔ new consensus tasks ensure multi-agent interplay (future binding).
- **L2.15 Self-Propagation** ↔ capsule + docs.
- **L2.16 Energy & Compute Ascension** ↔ not yet instrumented.

## Notes
- Need to codify explicit IDs (L2.1 etc) to map to enforcement.
- Some objectives currently unbound; bindings file should mark them as `todo` with rationale to avoid false sense of coverage.
- Format idea: YAML with sections `objectives` and `properties`, each entry capturing `id`, `summary`, `enforced_by`, `receipts`, `status`.
