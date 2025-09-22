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

For a single command that runs tests, refreshes receipts hygiene, reconciles task status, emits the operator preset receipt, logs a heartbeat, and (optionally) checks autonomy latency, use `python -m tools.agent.batch_refinement --task <id> [--agent <id>] [--pytest-args ...]`. The helper stops on the first failure, writes the receipt path to stdout, and returns non-zero if pytest fails, task synchronization trips, or hygiene cannot complete. Each run also records a JSON summary under `_report/usage/batch-refinement/` so auditors can replay the batch, plus a rolling `summary.json` that tracks averages, missing-receipt runs, and the latest batch metadata for automation to consume.

- `--fail-on-missing` and `--max-plan-latency <seconds>` pass straight through to the hygiene bundle so batches halt when receipts drift.
- Logs capture runtime metrics (`pytest_seconds`, `hygiene_seconds`), task synchronization deltas, the refreshed autonomy status receipt under `_report/usage/autonomy-status.json`, the heartbeat payload recorded on the coordination bus, and any autonomy latency alerts generated during the run.

### Batch refinement log summary

Use `python -m tools.agent.batch_report [--limit N] [--json]` to list recent batch receipts. The CLI reads `_report/usage/batch-refinement/*.json`, surfaces the operator preset outcome, missing-receipt counts, and the slowest plan, and can emit structured JSON for downstream automation. When available, the runner’s `summary.json` provides a rolling average so batch_report can highlight longer-term drift without reading every log.

### Autonomy status digest

`python -m tools.agent.autonomy_status [--limit N] [--json]` combines the latest receipts hygiene summary with recent batch logs, highlighting missing receipts, slow plans, and recent batch outcomes in one place. Each run also writes `_report/usage/autonomy-status.json` (unless `--no-write` is supplied) with averaged runtime metrics from recent batch runs.

### Autonomy latency sentinel

Run `python -m tools.agent.autonomy_latency --threshold 3600` to alert on any plan whose receipts latency exceeds the configured number of seconds. The sentinel reads `_report/usage/autonomy-status.json`, mirrors offending plan ids onto the coordination bus as `alert` events, and writes a receipt (`_report/usage/autonomy-latency.json` by default) summarising alert payloads. Use `--dry-run` to inspect without logging events and `--no-write` to skip receipt emission. Batch refinement can also invoke this sentinel automatically via `--latency-threshold` (adding `--latency-dry-run` to avoid logging).

### Case study: VDP guard pilot (2025-09-21)

**Objective.** Treat a volatile market brief as the pilot lane for pushing TEOF toward platform-level adoption.

- **Commands run:**
  - `teof brief` → `artifacts/ocers_out/20250921T214419Z/brief.json` (fresh ensemble receipts).
  - `python3 scripts/ci/check_vdp.py` → `_report/case-studies/vdp_guard_check.txt` (no violations).
  - `pytest tests/test_vdp_guard.py tests/test_ci_check_vdp.py` → `_report/case-studies/vdp_guard_pytest.txt` (7 tests, all green).
- **Receipts referenced:** plan `2025-09-21-vdp-pilot-case-study` (S2), plus the CI outputs above. All receipts are tracked in git via `_report/case-studies/` to keep audit hooks stable.
- **Outcome:** guard stack blocked zero regressions, produced deterministic artifacts, and documents the adoption blueprint now living in `docs/workflow.md`.

Use this pattern when pitching TEOF as a top-layer guard: pick a high-risk workflow, run the guard chain, log the receipts, and point stakeholders to the plan + case-study appendix.

### External receipt adapter (design draft)

To bridge real-world feeds into TEOF without breaking provenance:

- **Key generation (`python -m tools.external.keys` or `teof-external-keygen`)** — create an Ed25519 key pair, write the public half under `governance/keys/<key_id>.pub`, and capture the anchors event before streaming receipts.
- **CLI surface (`python -m tools.external.adapter` or `teof-external-adapter`)**
  - Required flags: `--feed-id`, `--plan-id`, `--input` (structured data or CSV), `--out _report/external/<feed>/<ts>.json` (default auto-generated), `--key governance/keys/<id>.ed25519`.
  - Optional: `--meta key=value` passthrough for domain hints.
- **Processing flow**
  1. Load raw observations, normalize to the VDP-ready form (`label`, `value`, `timestamp_utc`, `source`, `volatile`, `stale_labeled`).
  2. Canonicalize JSON (sorted keys, UTF-8, newline) and compute `hash_sha256`.
  3. Sign with Ed25519 (per L6 canon) and emit the receipt envelope:

```json
{
  "feed_id": "geopolitics",
  "plan_id": "2025-09-21-vdp-pilot-case-study",
  "issued_at": "2025-09-21T22:05:00Z",
  "observations": [
    {"label": "FX:USD-RUB", "value": 96.4, "timestamp_utc": "2025-09-21T22:00:00Z", "source": "https://api.fx.example/usd-rub", "volatile": true, "stale_labeled": false}
  ],
  "hash_sha256": "…",
  "signature": "base64url(ed25519_signature)",
  "public_key_id": "feed-geopolitics-2025"
}
```

- **Registration workflow**
  1. Generate an Ed25519 key pair; store the public half under `governance/keys/<key_id>.pub` with an anchors entry.
  2. Open a plan describing feed scope, steward, retention window, and rollback steps.
  3. Land adapter code/tests and extend `scripts/ci/check_vdp.py` to verify `_report/external/<feed>/*.json` signatures.
  4. Update `governance/core/L4 - architecture/bindings.yml` coverage once verification exists.

- **Failure modes**
  - Invalid signature → adapter exits non-zero, writes diagnostic receipt, posts `bus_event --event alert`.
  - Stale data (>24h) → adapter flags `stale_labeled` or aborts unless plan explicitly authorizes replay.

This spec guides S2 of `_plans/2025-09-21-automation-governance-upgrade`: implement the adapter, verification hook, and tests so external feeds can plug into TEOF without breaking provenance.

### External feed summary CLI

Use `python -m tools.external.summary --threshold-hours 24 --out _report/usage/external-summary.json` (or the packaged `teof-external-summary`) to emit KPI metrics for receipts stored under `_report/external/`. The JSON includes:
- per-feed receipt counts, latest issuance timestamps, stale counts, invalid signature counters, and latest age in seconds
- a list of receipts that failed hash/signature validation

Run this after ingestion or during audits to surface drift; pass `--strict` to exit non-zero on any invalid receipts. The command underpins `_plans/2025-09-21-automation-governance-upgrade` (S3) and feeds dashboards documenting the guard’s efficacy.

## Open Questions

- Should automation maintain its own ledger of actions separate from `_report/`? (Potential future work.)
- How to encode confidence/calibration for automated decisions?
- When multiple bots disagree, who arbitrates? (Candidate: anchors events with human signatures.)

Automation extends workflow without creating a new authority: it accelerates mundane actions, but humans and higher layers remain the governors of meaning and safeties.
