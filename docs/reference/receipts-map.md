<!-- markdownlint-disable MD013 -->
# Receipts Map

Status: Advisory  
Systemic targets: S1, S4, S6  
Layer targets: L4, L5, L6

Use this map to keep receipt hygiene predictable. Every agent session should
touch only the lanes below unless a Meta-TEP introduces a new surface.

## Active Lanes

| Folder | Purpose | Typical Writers / Commands | Notes |
| --- | --- | --- | --- |
| `_report/agent/<agent-id>/` | Seat-scoped receipts (session boot, bus status, plan runs, governance notes). | `python -m tools.agent.session_boot`, `python3 -m teof bus_event`, `teof scan --out`, autonomy/coordinator helpers. | Keep subfolders predictable: `session_guard/`, `runs/`, `governance/`, `feedback/`, `analysis/`. |
| `_report/planner/validate/` | Plan validator summaries, queue warnings. | `python -m tools.planner.validate --strict`, planner CLI `list/status`. | Attach summaries to plans and memory entries; CI reads the latest JSON for health checks. |
| `_report/usage/` | Shared dashboards, hygiene reports, and longitudinal metrics (autonomy status, receipts index, ratchet history). | `python -m tools.agent.receipts_hygiene`, `teof scan --out`, `python -m tools.metrics.plan_lattice`, `python -m tools.agent.autonomy_status`. | Treat as the canonical “observatory”—one subfolder/file per product. Avoid personal notes here. |
| `_report/usage/receipt-graph/` | Observation lineage graphs, Mermaid exports, and run receipts capturing queue→claim→plan→event→memory linkage. | `python -m tools.observation.receipt_graph` (writes graph JSON, optional `.mmd`, and `receipt_graph-run-*.json` plus `run-latest.json`). | Keep one graph per run (timestamped) and let automation tail `run-latest.json` when validating ND-053. Use `--no-receipt` only for synthetic tests that already emit receipts elsewhere. |
| `_report/usage/plan-scope/` | Per-plan scope manifests + freshness receipts proving worktree isolation before pushes. | `python -m teof plan_scope --plan <id> [--manifest …]` (default run emits `plan-scope-<plan>-<ts>.json` + `latest.json`). | Reference these receipts in plans/backlog reviews to prove queue hygiene; relocation requires updating `docs/automation/plan-scope.md` + CI guards. |
| `docs/usage/capability-heartbeat/` | Git-tracked heartbeat receipts proving key CLIs still run even when `_report/` is ignored. | `python -m teof plan_scope … --receipt-dir docs/usage/capability-heartbeat`, `python -m teof receipts_stream … --receipt …`, `python -m teof receipts_stream_guard … --receipt …`, `python -m teof scan_history … --receipt-path …`. | Keep one timestamped file per CLI run plus a `latest.json` pointer so capability inventory checks can cite stable artifacts without depending on ignored paths. |
| `docs/usage/capability-heartbeat/` | Public heartbeat receipts proving key CLI commands have been exercised recently even when `_report/` is ignored. | `python -m teof plan_scope … --receipt-dir docs/usage/capability-heartbeat`, `python -m teof receipts_stream … --receipt …`, `python -m teof receipts_stream_guard … --receipt …`, `python -m teof scan_history … --receipt-path …`. | Keep each receipt timestamped and maintain `latest.json` so the capability inventory guard can point at tracked evidence. |
| `_report/ethics/guards/` | Canonical ethics guard receipts (consent/review JSON emitted by guard CLIs). | `python -m tools.autonomy.ethics_gate --out …`, `teof scan --emit-bus`, CI guard scripts. | Keep receipts under dated subfolders (e.g., `_report/ethics/guards/2025-11-09/`). The CLI auto-detects these paths for frontier/ethics scans even if plans forget to list them, so never relocate the files without updating automation. |
| `_report/analysis/memory-gap/` | Memory guard receipts showing which plans lack log coverage. | `python -m tools.memory.gap_audit`, `scripts/ci/check_memory_gap.py`. | Include timestamps + filters (since/window-hours) in filenames. CI expects `latest.json` (manual) and `ci-latest.json` (guard) to exist for audits referenced in plans. |
| `_report/manager/` | Manager cadence reports, severity digests. | `python -m tools.agent.manager_report`, `python -m tools.agent.coord_dashboard`. | Each run writes a timestamped markdown summary; managers should link these in memory/log and plan receipts. |
| `_report/consensus/` | Consensus summaries, quorum receipts, ledgers feeding capsule release. | `scripts/ci/consensus_smoke.sh`, `python -m tools.autonomy.consensus_dashboard`. | Required before capsule promotions; reference in plans and anchors. |
| `_report/capsule/` | Capsule cadence checks and release evidence. | `python -m tools.autonomy.capsule_cadence`, `scripts/ci/check_capsule_cadence.py`. | Append-only per release cycle; pair with governance anchors. |
| `_report/external/` | Signed receipts from external feeds, adapters, authenticity checks. | `python -m tools.external.adapter`, `scripts/ci/check_vdp.py` (verification). | Files must include hashes + signatures; CI rejects unsigned payloads. |
| `_report/fractal/` | Fractal conformance guard outputs and advisories. | `scripts/ci/check_fractal_conformance.py`. | Consume advisories before opening new hygiene work. |
| `_report/runner/` | Command receipts from `tools/runner` and wrapper CLIs. | `python -m tools.runner`, automation harnesses. | Each entry is a timestamped JSON describing command, exit code, stdout/stderr. |
| `_report/session/` | Session guard receipts (dirty handoff, overrides). | `python -m tools.agent.session_boot --with-status`, session guard hooks. | Include these when documenting handoffs in memory/log. |

## Shelved / Historical Lanes

Keep the directories below for provenance; **do not** drop new receipts unless a
Meta-TEP revives them.

| Folder | Status | Notes |
| --- | --- | --- |
| `_report/autonomy/` | Legacy | Early backlog synth prototypes; superseded by `_report/usage/autonomy-*`. |
| `_report/case-studies/` | Frozen | Static artifacts from VDP/guard exploration. Reference only when replaying historical analyses. |
| `_report/guard/` | Sandbox | Experimental guard demos (e.g., sandbox-demo). Use `_report/usage/` for current guard outputs. |
| `_report/systemic_ai/` | Archive | Placeholder for retired systemic AI explorations. Keep read-only until revived via plan + Meta-TEP. |
| `_report/runner_test/` | Legacy QA | Obsolete runner fixtures. Prefer `_report/runner/`. |

If you find another orphan lane, log an observation in `memory/log.jsonl`, then
propose a cleanup plan before deleting or reviving it.

## Memory & Cross-Links

- **Primary log:** `memory/log.jsonl` (append-only via `tools/memory/log-entry.py`).
- **Hot index:** `memory/hot_index.jsonl` for faster queries (`python -m tools.memory.hot_index`).
- Every plan or automation receipt should link to relevant `_report/...` artifacts
and memory entries so auditors can replay the exact trail.

## Adding a New Lane

Only add a new receipts directory when all of the following hold:
1. No existing lane fits the evidence you need to store.
2. There is a plan + owner committing to maintain the lane.
3. A Meta-TEP updates `docs/architecture.md` (or a linked canonical doc) and the
   guard matrix so automation knows about the new location.

When in doubt, default to `_report/agent/<agent>` (personal runs) or
`_report/usage/` (shared dashboards). Minimal, predictable surfaces make it
easier for new agents to onboard and for CI to prove the work happened.
