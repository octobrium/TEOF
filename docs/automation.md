# L6 Automation (Working Notes)

**Purpose:** describe how automated actors (bots, scripts, agents) operate inside TEOF while serving L0–L5.

## Core Duties

1. **Obey upper layers.** Automation inherits obligations from Observation (L0) through Workflow (L5); it may not bypass safeties or append-only rules.
2. **Emit receipts.** Every automated action must generate auditable receipts (`_report/…`) and, when appropriate, link to plans or memory entries.
3. **Expose capabilities.** Bots publish what they can do (e.g., `autocollab`, `ledger`) via hello packets or README snippets so peers know when to trust them.
4. **Stay reversible.** Prefer actions that can be rolled back or replayed from receipts; if irreversibility is unavoidable, require human checkpointing.
5. **Request consent signals.** When touching shared governance (anchors, capsules), automation should wait for maintainers or policy scripts to confirm.

## Operational Modes

- **Fast lane:** low-risk tasks (e.g., queue hygiene, ledger append) with auto receipts and immediate logging.
- **Guarded lane:** higher-risk operations require an open plan step and manual approval before execution.
- **Dissent lane:** if automation detects conflicts (hash mismatches, policy failures), it pauses, emits a warning, and prompts human review.

## Interfaces

- **Hello packet:** `tools/reconcile_hello.py` – publish hashes + capabilities.
- **Diff + Fetch:** `tools/reconcile_diff.py`, `tools/reconcile_fetch.py` – reconcile across instances.
- **Plans:** automation should claim steps via `tools/planner.cli step set …` so provenance is consistent.

### Receipts index

Run `python -m tools.agent.receipts_index --output receipts-index.jsonl` to emit a JSONL ledger covering `_plans/*.plan.json`, `_report/**` receipts, and manager-report entries. Relative `--output` paths land under `_report/usage/`; omit `--output` to stream to stdout. Each record includes basic metadata (timestamp, size, sha256) and flags receipts that are missing or untracked so you can repair evidence before CI fails `check_plans`. Automation can ingest the ledger to power hygiene sweeps or surface stale subsystems.

### Receipts latency

To measure how quickly reflections turn into evidence, run `python -m tools.agent.receipts_metrics --output receipts-latency.jsonl`. The CLI reuses the receipts ledger, computes deltas between plan creation, manager-report notes (`meta.plan_id`), and the first/last receipts, and writes per-plan metrics (including missing receipts). Relative output paths also land under `_report/usage/`.

### Receipts hygiene bundle

Need both artifacts in one go? `python -m tools.agent.receipts_hygiene` runs the indexer and latency metrics together, writes `_report/usage/receipts-index-latest.jsonl`, `_report/usage/receipts-latency-latest.jsonl`, and a summary (`receipts-hygiene-summary.json`) listing missing receipts and the slowest plans. Batch refinement mode expects that summary plus the operator preset receipt from `python -m tools.agent.session_brief --preset operator` to anchor autonomous runs.

- `--fail-on-missing` exits non-zero if any plan lacks receipts.
- `--max-plan-latency <seconds>` exits non-zero if `plan_to_first_receipt` or `note_to_first_receipt` exceeds the threshold.

### Batch refinement runner

For a single command that runs tests, refreshes receipts hygiene, reconciles task status, emits the operator preset receipt, logs a heartbeat, and (optionally) checks autonomy latency, use `python -m tools.agent.batch_refinement --task <id> [--agent <id>] [--pytest-args ...]`. The helper stops on the first failure, writes the receipt path to stdout, and returns non-zero if pytest fails, task synchronization trips, or hygiene cannot complete. Each run also records a JSON summary under `_report/usage/batch-refinement/` so auditors can replay the batch.

- `--fail-on-missing` and `--max-plan-latency <seconds>` pass straight through to the hygiene bundle so batches halt when receipts drift.
- Logs capture runtime metrics (`pytest_seconds`, `hygiene_seconds`), task synchronization deltas, the refreshed autonomy status receipt under `_report/usage/autonomy-status.json`, the heartbeat payload recorded on the coordination bus, and any autonomy latency alerts generated during the run.

### Batch refinement log summary

Use `python -m tools.agent.batch_report [--limit N] [--json]` to list recent batch receipts. The CLI reads `_report/usage/batch-refinement/*.json`, surfaces the operator preset outcome, missing-receipt counts, and the slowest plan, and can emit structured JSON for downstream automation.

### Autonomy status digest

`python -m tools.agent.autonomy_status [--limit N] [--json]` combines the latest receipts hygiene summary with recent batch logs, highlighting missing receipts, slow plans, and recent batch outcomes in one place. Each run also writes `_report/usage/autonomy-status.json` (unless `--no-write` is supplied) with averaged runtime metrics from recent batch runs.

### Autonomy latency sentinel

Run `python -m tools.agent.autonomy_latency --threshold 3600` to alert on any plan whose receipts latency exceeds the configured number of seconds. The sentinel reads `_report/usage/autonomy-status.json`, mirrors offending plan ids onto the coordination bus as `alert` events, and writes a receipt (`_report/usage/autonomy-latency.json` by default) summarising alert payloads. Use `--dry-run` to inspect without logging events and `--no-write` to skip receipt emission. Batch refinement can also invoke this sentinel automatically via `--latency-threshold` (adding `--latency-dry-run` to avoid logging).

## Open Questions

- Should automation maintain its own ledger of actions separate from `_report/`? (Potential future work.)
- How to encode confidence/calibration for automated decisions?
- When multiple bots disagree, who arbitrates? (Candidate: anchors events with human signatures.)

Automation extends workflow without creating a new authority: it accelerates mundane actions, but humans and higher layers remain the governors of meaning and safeties.
