# L6 Automation (Working Notes)

**Purpose:** describe how automated actors (bots, scripts, agents) operate inside TEOF while serving L0–L5. Automation now documents explicit systemic targets (S1–S10) and layer coordinates (L0–L6); see [`docs/automation/systemic-overview.md`](systemic-overview.md) and [`docs/foundation/systemic-scale.md#hierarchy-enforcement`](../foundation/systemic-scale.md#hierarchy-enforcement)). Automation must record which higher axes (Unity → Power) are satisfied before lower-axis guards (Ethics, Freedom, Meaning) escalate.

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

### Reflections overview

`teof reflections` prints a quick audit of `memory/reflections/`: totals, latest capture time, layer coverage, and top tags. Use `--layer`, `--tag`, or `--days` filters to focus on a subset and `--limit` to cap the table rows. Pass `--format json` when automation needs the structured payload (summary + selected reflections) instead of the table view.

### Receipts hygiene bundle

Need both artifacts in one go? `python -m tools.agent.receipts_hygiene` runs the indexer and latency metrics together, writes `_report/usage/receipts-index-latest.jsonl`, `_report/usage/receipts-latency-latest.jsonl`, and a summary (`receipts-hygiene-summary.json`) listing missing receipts and the slowest plans. Batch refinement mode expects that summary plus the operator preset receipt from `python -m tools.agent.session_brief --preset operator` to anchor autonomous runs.

- `--fail-on-missing` exits non-zero if any plan lacks receipts.
- `--max-plan-latency <seconds>` exits non-zero if `plan_to_first_receipt` or `note_to_first_receipt` exceeds the threshold.
- `--warn-plan-latency <seconds>` (default **259200s**, 3 days) annotates slow plans with `severity="warn"` in `slow_plan_alerts`.
- `--fail-plan-latency <seconds>` (default **604800s**, 7 days) raises a non-zero exit and records `severity="fail"` when breached.

### Systemic scan bundle

`teof scan` runs the frontier, critic, TMS, and ethics guardrails together so humans get a single systemic readiness snapshot.

```bash
teof scan --out _report/usage/systemic-scan --format json --emit-bus --emit-plan
```

- Writes `frontier.json`, `critic.json`, `tms.json`, and `ethics.json` into the chosen directory with matching `receipt_sha256` fields.
- Summaries land on stdout (table by default, JSON when `--format json` is set) with per-axis counts for each subsystem.
- `--emit-bus` seeds repair claims for critic/ethics findings when receipts are captured; `--emit-plan` adds TMS plan skeletons that inherit the receipt path.
- Use `--limit` to cap frontier entries (default **10**). Skipping `--out` keeps the run read-only.
- Scope the run with `--only <component>` (repeat for multiple) or `--skip <component>` to evaluate a subset. Component names: `frontier`, `critic`, `tms`, `ethics`.
- Pass `--summary` to print a quick counts list instead of full tables when you only need systemic readiness tallies.
- Capture a fresh manager-report tail before automation runs (`python -m tools.agent.session_boot --agent <id> --with-status`) so the session guard sees the latest coordination receipts. CI jobs should run `session_boot` in the same step as the scan.

### Dynamic scan driver

`teof-scan-driver` chooses which guards to run by inspecting tracked inputs, then delegates to `teof scan` and logs each decision under `_report/usage/scan-history.jsonl`.

```bash
teof-scan-driver --summary --emit-bus
```

- Tracked files: `_plans/next-development.todo.json`, `agents/tasks/tasks.json`, `memory/state.json`.
- Each fingerprint captures both `mtime_ns` and a SHA-256 digest so unchanged writes do not trigger redundant guards.
- Triggers: changes to backlog/tasks run **frontier** and **ethics**; changes to backlog/state run **critic**; state changes run **tms**.
- Policy lives at `docs/automation/scan-policy.json`; override with `--policy <path>` for custom mappings or alternative guard sets.
- Repeat `--force <component>` to include guards even when inputs are unchanged; use `--skip <component>` to suppress a guard for the current iteration.
- `--dry-run` prints the planned command and still records the decision in history so operators can rehearse policies without executing guards.

### Reactive scan trigger

`python -m tools.autonomy.scan_trigger` checks `git status --porcelain` and runs the scan driver only when watched paths change (defaults: `_plans/`, `_report/`). Use `--dry-run` to report without executing, `--no-summary` to request full scan output, or repeat `--watch <prefix>` to monitor more directories. Ideal for git hooks or CI steps where you want evidence-driven triggers instead of blind schedules; each run prints whether a scan executed and why.

### Coordinator manifest builder

`python -m tools.autonomy.coordinator_manager --plan <plan_id> --step <step_id>` generates a manifest summarising the work package a downstream agent should execute. The manifest captures plan metadata, recommended guard commands (status/scan/tasks foreman calls), and the receipts the worker is expected to emit. Output defaults to `_report/agent/<agent>/manifests/manifest-<UTC>.json`; pass `--out` to control the path, `--commands-json` to supply bespoke command lists, or `--agent-id` when drafting manifests for another seat. Use this before dispatching autonomous workers so assignments stay auditable and consistent with the alignment trail.

### Coordinator worker harness

`python -m tools.autonomy.coordinator_worker <manifest.json>` validates a manifest and runs through the recorded command list. By default it prints the sequence (dry-run); add `--execute` to run the commands, enforce a fresh session via the guard, and emit a run receipt under `_report/agent/<agent>/<plan>/runs/run-<UTC>.json`. Use `--allow-stale-session` only when you have a companion receipt documenting the override. This harness is the foundation for fully autonomous worker agents that keep receipts in sync with the coordinator manager outputs.

### Coordinator guardrail loop

Planned orchestration will pin guardrails around every coordinator run:

- `session_boot` freshness enforced before any manager or worker action (`session_guard` hook stays in place).
- `tools.autonomy.scan_trigger` pre/post each work order to surface drift only when inputs change.
- `extensions.validator.teof_systemic_min` applied to manifests and resulting plan diffs to make sure assignments stay truth-aligned.
- Circuit breaker receipts (`_report/agent/<manager>/state.json`) that pause automation when scans or systemic checks fail.
- Bus notes summarising guard outcomes so humans can monitor without crawling logs.

Once the loop is wired, automation can dispatch workers without human hand-offs while keeping observation, guardrails, and reversibility intact.

### Coordinator orchestrator

`python -m tools.autonomy.coordinator_orchestrator --plan <plan_id> --step <step_id>` claims an optional task, runs the guard loop with `--execute`, and handles session freshness automatically. Pass `--task-id`/`--branch` when you want the orchestrator to file the bus claim before execution, `--worker-agent` to dispatch a different worker seat, or `--dry-run` to review planned actions. This is the entrypoint future autonomous manager agents will call to keep the coordinator pipeline fully automated.

### Coordinator loop

`python -m tools.autonomy.coordinator_loop` loads `_plans/next-development.todo.json`, finds the first pending item with a viable plan step, and hands it to the orchestrator. Use `--iterations N` or `--sleep SECONDS` for watch-mode, `--dry-run` to preview selections, and `--manager-agent/--worker-agent` to pin seats. This is the minimal heartbeat for plug-and-play donors: point a worker at the repo, run the loop, and TEOF coordinates the rest.

### Coordinator service

For a long-running seat, start `python -m tools.autonomy.coordinator_service --interval 60 --log`. It refreshes the session, invokes the loop once per interval, records a receipt for each iteration, and stops automatically on guard failures so humans can inspect the receipts. Combine this with `systemd`, launchd, or a tmux session to keep plug-and-play agents online with minimal babysitting.

### Commitment guard

Use `python -m tools.autonomy.commitment_guard` to scan `_bus/messages/**/*.jsonl` and `_report/usage/reflection-intake/*.md` for phrases such as “next time” or “mental note”. Any matches indicate a promise that must be captured as a plan, TODO, or receipt.

Call the script before ending a session to keep the Integrity Gap metric honest. Combine it with `docs/usage/direction-metrics.md` so TTΔ escalations include missing artifacts.

### Batch refinement runner

For a single command that runs tests, refreshes receipts hygiene, reconciles task status, emits the operator preset receipt, logs a heartbeat, and (optionally) checks autonomy latency, use `python -m tools.agent.batch_refinement --task <id> [--agent <id>] [--pytest-args ...]`. The helper stops on the first failure, writes the receipt path to stdout, and returns non-zero if pytest fails, task synchronization trips, or hygiene cannot complete. Each run also records a JSON summary under `_report/usage/batch-refinement/` so auditors can replay the batch, plus a rolling `summary.json` that tracks averages, missing-receipt runs, and the latest batch metadata for automation to consume.

- `--fail-on-missing` and `--max-plan-latency <seconds>` pass straight through to the hygiene bundle so batches halt when receipts drift.
- Logs capture runtime metrics (`pytest_seconds`, `hygiene_seconds`), task synchronization deltas, the refreshed autonomy status receipt under `_report/usage/autonomy-status.json`, the heartbeat payload recorded on the coordination bus, and any autonomy latency alerts generated during the run.
- `--latency-warn-threshold` / `--latency-fail-threshold` let you forward custom thresholds to the latency sentinel; omit them to fall back to the defaults.

### Batch refinement log summary

Use `python -m tools.agent.batch_report [--limit N] [--json]` to list recent batch receipts. The CLI reads `_report/usage/batch-refinement/*.json`, surfaces the operator preset outcome, missing-receipt counts, and the slowest plan, and can emit structured JSON for downstream automation. When available, the runner’s `summary.json` provides a rolling average so batch_report can highlight longer-term drift without reading every log.

### Autonomy status digest

`python -m tools.agent.autonomy_status [--limit N] [--json]` combines the latest receipts hygiene summary with recent batch logs, highlighting missing receipts, slow plans, and recent batch outcomes in one place. Each run also writes `_report/usage/autonomy-status.json` (unless `--no-write` is supplied) with averaged runtime metrics from recent batch runs.

- **Receipt example:** see `_plans/2025-09-21-autonomy-status-receipt.plan.json` and `_report/usage/autonomy-status.json` (attached 2025-09-22) for a live artifact. It includes top-slow plans, warn/fail counts, and links to batch logs.
- **Adoption KPI:** IRL deployments should track how often the status is generated (target: daily or per batch) and ensure warn/fail counts are triaged via the coordination bus.

### Autonomy latency sentinel

Run `python -m tools.agent.autonomy_latency --warn-threshold 259200 --fail-threshold 604800` to alert on plans whose receipts latency exceeds the configured bounds. The sentinel reads `_report/usage/autonomy-status.json`, mirrors offending plan ids onto the coordination bus as `alert` events (severity `warn` or `high`), and writes a receipt (`_report/usage/autonomy-latency.json` by default) summarising alert payloads and counts by severity. Use `--dry-run` to inspect without logging events and `--no-write` to skip receipt emission. `--threshold` remains available as a shorthand when warn/fail share the same value. Batch refinement can also invoke this sentinel automatically via `--latency-warn-threshold` / `--latency-fail-threshold` (adding `--latency-dry-run` to avoid logging).

### Case study: VDP guard pilot (2025-09-21)

**Objective.** Treat a volatile market brief as the pilot lane for pushing TEOF toward platform-level adoption.

- **Commands run:**
  - `teof brief` → `artifacts/systemic_out/20250921T214419Z/brief.json` (fresh ensemble receipts).
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
- per-feed receipt counts, latest issuance timestamps, stale counts, invalid signature counters, and latest ages (seconds + hours)
- a trust bundle (`score`, `status`, `signals`) that condenses freshness/signature health into an alignment score
- a list of receipts that failed hash/signature validation
- optional operator notes when you pass `--notes-json <path>` (map `feed_id` → commentary for reviewers)
- a `stewards` index summarising each steward’s obligations, capabilities, trust baseline, and the feeds they cover
- when notes are provided, `_report/usage/external-feedback.json` is generated as a compact ledger of commentary + trust context for follow-up reviews

Run this after ingestion or during audits to surface drift; pass `--strict` to exit non-zero on any invalid receipts. The command underpins `_plans/2025-09-21-automation-governance-upgrade` (S3) and feeds dashboards documenting the guard’s efficacy.
For hygiene sweeps, `python -m tools.external.registry_check` verifies that every registry row, config entry, and summary record stays in sync.

### Authenticity dashboard

For tier-level visibility, run `python -m tools.external.authenticity_report` (optionally passing `--summary`, `--feedback`, `--out-md`, `--out-json`). The tool consumes `_report/usage/external-summary.json` + `_report/usage/external-feedback.json` and emits:
- `_report/usage/external-authenticity.md` – markdown snapshot with tier weights, counts, and attention feeds
- `_report/usage/external-authenticity.json` – structured data for downstream automation

The summary CLI already regenerates both files after each run; use the command above only when you need to recompute dashboards from archived data.
The Markdown dashboard is also mirrored to `docs/usage/external-authenticity.md` so STATUS reports and docs stay aligned with the latest run.
When a tier’s adjusted trust drops below `--auth-alert-threshold` (default `0.6`) or any feed enters an attention state, the summary CLI logs a bus status event (`teof-auth-monitor`) so managers can react immediately. The same run now also feeds `tools.agent.authenticity_escalation`, which keeps streak state under `_report/agent/teof-auth-monitor/` and, after two consecutive degraded runs, auto-assigns steward tasks (`AUTH-<tier>-<steward>-<date>`) via the bus to force remediation.

### Autonomy self-prompt loop

With authenticity + CI guardrails satisfied, automation can safely claim the next development task by running:

```bash
python3 -m tools.autonomy.next_step --claim
```

The command consults `_plans/next-development.todo.json`, verifies authenticity trust (≥ configured threshold, no attention feeds), confirms planner summary exit code is `0`, and then marks the first `status: "pending"` item as `in_progress` while logging the selection under `_report/usage/selfprompt/`. Plan `2025-09-23-selfprompt-pilot` captures receipts for dry runs and documents rollback expectations before unattended execution becomes canon.
Agents can consult `_plans/next-development.todo.json` and run `python -m tools.autonomy.next_step --claim` to adopt the next sanctioned refinement once authenticity and CI guardrails pass.

Auto-proceed runs are controlled by `docs/automation/autonomy-consent.json`. That policy records whether the loop is enabled (`auto_enabled`), how many iterations to attempt (`max_iterations`), and whether write-mode is allowed (`allow_apply`). Update the file (and commit the change) to toggle automation on/off; by default the loop halts whenever authenticity attention feeds appear or CI stops passing. When auto mode is active, use:

```bash
python3 -m tools.autonomy.next_step --auto --execute
```

Receipts for each unattended iteration land under `_report/usage/selfprompt/` and `_report/usage/autonomy-actions/`, so future agents can audit what changed and disable the policy if needed.

### Background autonomy loop

To keep the unattended loop running without external schedulers, launch the repo-native supervisor:

```bash
python3 -m tools.autonomy.auto_loop --background --sleep 30
```

The helper honours the consent policy, records a PID under `_report/usage/autonomy-loop/auto-loop.pid`, streams logs to `_report/usage/autonomy-loop/auto-loop.log`, and exits automatically once the backlog empties (or when guardrails trip). Add `--watch` if you want it to keep polling for new work, use `--tail N` to inspect logs, and `--status` / `--stop` to manage it. Background cycles generate the same receipts and backlog updates as manual invocations, ensuring the audit trail stays intact.

### Autonomy conductor prompts

Use `teof-conductor --watch --dry-run --max-iterations 0` (or `python3 -m tools.autonomy.conductor ...`) to stream guarded Codex prompts without human typing. Each cycle records `_report/usage/autonomy-conductor/conductor-*.json` capturing the backlog item, diff/test guardrails, authenticity + planner snapshots, and the generated prompt. Provide `--plan-id <ND-###>` to focus on a single task; the conductor automatically relinquishes the claim if the selection does not match. Add `--emit-prompt` to print the rendered prompt to stdout, or `--emit-json` to pipe the full payload to other automation. Combine with a background loop (or scheduler) when you want continuous prompting while keeping policy guardrails visible in receipts.

### Objectives status snapshot

Run `teof-objectives-status --window-days 7 --out _report/usage/objectives-status.json` to summarise the health of key L2 objectives (reflections cadence, autonomy cycles, authenticity trust, external sensing freshness). The CLI scans existing receipts and reports whether current activity meets the minimum cadence targets defined in `docs/vision/objectives-ledger.md`.

### Backlog depletion guard

Run `python -m tools.agent.backlog_health --threshold 3 --candidate-limit 5 --fail-on-breach` to watch `_plans/next-development.todo.json`. When the pending backlog falls below the threshold the guard writes a receipt under `_report/usage/backlog-health/` and recommends queue entries to replenish the worklist. See [`docs/automation/backlog-health.md`](automation/backlog-health.md) for the full guide.

### Backlog steward

`python -m tools.autonomy.backlog_steward --apply` inspects `_plans/next-development.todo.json`, compares each item with its referenced plan, and marks entries as `done` when the plan (and its receipts) reach completion. It assembles the supporting receipts automatically, updates the backlog timestamp, and writes a receipt under `_report/usage/backlog-steward/`. Run without `--apply` to preview changes.

### Log real-world impact

Use `python3 -m tools.receipts.log_event impact --title "Outcome" --value 100 --description "..." --receipt <path>` to append structured impact entries under `memory/impact/log.jsonl`. Promote notable items into the impact ledger so Objective O4 stays tied to receipts and measurable value.

### External feed adoption playbook

**Value proposition.**
- **Proofable ingestion:** every volatile claim arrives with timestamp, source, hash, and signature, so reviewers can trust third-party feeds without re-ingesting raw APIs.
- **Incremental rollout:** adapters run from the command line, push receipts into `_report/external/`, and surface their health via `_report/usage/external-summary.json`—no new infrastructure required.
- **Business KPIs:** feeds report receipt counts, freshness, and invalid signature rates; automation dashboards and changelog tie those metrics to release readiness.

**Integration steps (minimum viable pilot).**
1. Generate a key pair (`teof-external-keygen --key-id <feed>`) and anchor the public key.
2. Open a plan describing scope, steward, and rollback (`_plans/<date>-<feed>-pilot.plan.json`).
3. Run the adapter (`teof-external-adapter --feed-id <feed> --plan-id <plan> --input <data>.json --refresh-summary`) so the summary + registry update immediately after the receipt lands.
4. Verify receipts with `scripts/ci/check_vdp.py` and capture the KPI summary (`teof-external-summary`).
5. Attach receipts to the plan; publish a case study (similar to `_plans/2025-09-22-external-feed-demo.plan.json`).
6. Update the registry entry in [`docs/adoption/external-feed-registry.md`](../adoption/external-feed-registry.md) so the steward, key, latest receipt, and summary snapshot all point at the freshly signed run (either run `python -m tools.external.registry_update ...` directly or let `python -m tools.external.summary --registry-config docs/adoption/external-feed-registry.config.json` do it automatically).

**Candidate feed classes.**
- Market indicators (FX, commodities) sourced from read-only APIs.
- Geopolitical risk digests (curated RSS, analyst reports) normalized to VDP schema.
- Operational telemetry (service uptime, alert rates) when paired with signed emission keys.

**Adoption KPIs to track.**
- Mean/max receipt age per feed.
- Invalid signature count (should be zero); escalate the moment it isn’t.
- Time from raw observation → signed receipt → KPI summary (goal: < 5 minutes in steady state).
- Number of plans actively consuming each feed (shows business uptake).

**Packaging backlog.**
- Publish a pip extra (e.g., `pip install teof[external]`) that bundles PyNaCl and ships adapter/summary CLIs.
- Provide SDK stubs or REST examples so external partners can call the adapter programmatically.
- Automate dashboard generation from `_report/usage/external-summary.json` (Markdown/HTML) for exec reporting.

Use the playbook to scope real pilots: everything above runs with today’s toolkit; only the data source and plan context change. For a full checklist (including registry maintenance duties), see [`docs/adoption/external-feed-runbook.md`](../adoption/external-feed-runbook.md).

## Open Questions

- Should automation maintain its own ledger of actions separate from `_report/`? (Potential future work.)
- How to encode confidence/calibration for automated decisions?
- When multiple bots disagree, who arbitrates? (Candidate: anchors events with human signatures.)

Automation extends workflow without creating a new authority: it accelerates mundane actions, but humans and higher layers remain the governors of meaning and safeties.
