<!-- markdownlint-disable MD013 -->
Status: Living
Purpose: Process & checklists that enforce Architecture
Change process: PR + 1 maintainer
Review cadence: Monthly sweep

# TEOF Master Workflow (Minimal v1.3)

## Operator mode (LLM quick brief)

**Purpose:** Make any fresh session (human or assistant) act optimally to assess and advance TEOF with minimal surface area and deterministic, auditable outputs.

**Mission**
- Advance TEOF with minimal surface area and deterministic, auditable outputs.
- Follow the repo DNA, not ad-hoc preferences.

**Read these first (in order)**  
Use `docs/onboarding/README.md` as the orchestrator—automation and humans will
check that the sequence below is followed (for a consolidated command map, see [`docs/operator-atlas.md`](docs/operator-atlas.md)):
1) `docs/architecture.md` — where things go  
2) `docs/workflow.md` — priority ladder & release (this file)  
3) `docs/promotion-policy.md`  
4) `docs/quickstart.md` — one command → artifacts

**Guardrails**
- **Observation primacy:** do not propose rule changes until an end-to-end run path is clear.
- **Minimalism:** prefer the smallest change that makes the E2E path work.
- **Import policy:** no imports from `experimental/` or `archive/` inside `extensions/` (`scripts/policy_checks.sh`).
- **Provenance:** if you change the DNA (architecture/workflow/promotion-policy), propose an anchors event.
- **Hierarchy enforcement:** when guards conflict, satisfy higher systemic axes first (Unity → Meaning); see [`docs/foundation/systemic-scale.md#hierarchy-enforcement`](docs/foundation/systemic-scale.md#hierarchy-enforcement).

**DNA Guard Hook (Recommended)**

For agents working with TEOF, install the DNA guard hook to enforce observation-primacy behaviorally:

```bash
ln -sf ../../scripts/hooks/commit-msg-dna-guard .git/hooks/commit-msg
```

This hook blocks commits to DNA files (architecture.md, workflow.md, governance/) unless the commit message includes observation evidence (`Observed: git log <file>`, `Observed: memory/log.jsonl entry <hash>`, etc.). Closes the conceptual ≠ behavioral gap identified in transmission testing. See `scripts/hooks/README.md` for full documentation.

**Operating order**
1) Confirm structure matches `docs/architecture.md`.  
   - Run `teof operator verify` (core tier) to capture session + structure receipts before touching the bus. Add `--strict-plan` only when the run must also refresh the strict plan validator receipts for governance reviews.
2) Produce an E2E plan using `docs/quickstart.md` (exact commands, no guessing) and drop it in `_plans/` (`*.plan.json`). Validate with `python3 tools/planner/validate.py`.  
 2a) Run `python3 -m tools.agent.push_ready --require-test <receipt>` before pushing so the working tree, branch, claims, and receipts are captured with a readiness summary.  
 3) Verify enforcement: confirm `scripts/policy_checks.sh` and `scripts/ci/check_vdp.py` run in CI; the latter blocks volatile data without timestamps/sources using the fixtures in `datasets/goldens/`.  
  4) Triangulate gaps: if Quickstart or imports/paths are stale, propose the smallest patches to make them true.  
 4a) Rapid spikes belong in the sandbox lane: `teof-plan new <slug> --exploratory` writes to `_plans/exploratory/` with auto-expiry receipts under `_report/exploratory/`; run `python -m tools.planner.exploratory_lane --receipt --suggest` during hygiene sweeps to capture lane status and follow-up actions, then promote into the canonical lane once the experiment stabilizes.  
5) Output a prioritized plan (next 3–6 steps) to make the repo self-propagating (CLI → CI → freeze → docs).  
6) Seed `_bus/claims/<task>.json` before posting assignment/status bus messages: `python -m tools.agent.claim_seed --task <id> --agent <future-owner> --plan <plan-id> --branch agent/<future-owner>/<slug>` (check `--help` for `--status`/`--notes`). This keeps the `bus_message` claim guard satisfied; include a `python -m tools.agent.session_brief --task <id>` snippet in the assignment hand-off so the assignee can replay the staged context.  
7) After releasing a claim, run `python -m tools.agent.task_sync` so `agents/tasks/tasks.json` mirrors claim status.  
8) Only if rules block progress: propose a minimal DNA edit via a one-page Meta‑TEP (Problem, Proposal, Alternatives, Impact, Rollback).  
9) For external feeds, open a plan, register the signing key (anchors entry), build `python -m tools.external.adapter` receipts, and extend `scripts/ci/check_vdp.py` + dashboards before promoting.  
10) Keep plan receipts audited: run `python3 scripts/ci/check_plan_receipts_exist.py` regularly and log the summary under `_report/usage/` so missing/untracked evidence is caught early. Use `tools/agent/preflight.sh core|full` to separate observation (core) from workflow (operational) guards; each run drops `_report/usage/preflight/preflight-*.json` so we can monitor how often the heavier lane is needed (`python -m tools.usage.preflight_summary` rolls these receipts up for dashboards).
  - Draft the idea in `docs/proposals/` first (see `docs/proposals/readme.md`) so other seats can review before it graduates to a Meta‑TEP.
- Capture lattice health metrics with `python3 -m tools.metrics.plan_lattice --snapshot <yyyymmdd>` and attach the receipt under `_report/health/plan-lattice/` before starting new hygiene passes; when consolidating plans, append a cost entry per `docs/automation/plan-merge-ledger.md` so the `proportion_index` remains evidence-backed.
- Plan JSON must remain canonical: run `python3 -m tools.planner.validate` (or the CI guard) to ensure keys are unique—duplicate sections now fail fast so hygiene changes stay reversible.
- `python3 -m tools.planner.validate --strict` now enforces a *planner ratchet index*: the ratio of completed steps/claims to open work must stay ≥1.0. When the index drops, the validator exits non-zero and the CI guard blocks promotion until we either close outstanding plans or raise the ratchet with fresh receipts.
11) Before editing, review active claims via `python -m tools.agent.bus_status --active-only` (or the manager preset) so you coordinate with current owners instead of colliding; escalate on the bus when overlaps appear.  
12) When waiting on another seat, default to logged contributions: capture a reflection (`python -m tools.memory.cli note --summary "..."`) or draft the next plan (`teof-plan new <slug> --summary "..." --scaffold`) so idle windows still produce receipts.

**Review receipts lane**
- Log pending reviews with `python -m tools.agent.review request --id <slug> --summary "..." --artifact path` so `_report/reviews/<slug>/request-*.json` captures what’s blocking whom.
- Respond via `python -m tools.agent.review respond --id <slug> --status approved|changes_requested|info --notes "..."` to record approvals/rejections without routing through the user.
- Discover open work with `python -m tools.agent.review list --status pending` (uses `_report/reviews/**`) so reviewers can pick up requests without the user as intermediary.
- Watch `_report/reviews/` (future dashboard hook) to track throughput; this keeps review loops within Pattern C’s tactical lane while leaving a durable audit record.

**Response format**
- Summary (2–4 bullets)  
- Immediate actions (commands or file patches)  
- Risks / assumptions (short)  
- Next checkpoint (what to verify after the actions)


**Reference Helpers**
- Use `python3 -m tools.reference.lookup <keywords>` to pull citations from `docs/reference/quick-reference.md` without scanning the entire corpus.
- Mirror drill runbook: `docs/workflow/mirror-drill.md` (exercise Universal Mirrorhood across substrates every 30 days).
**Non-goals**
- No new CI rules unless they protect the kernel import boundary.
- No new top-level folders unless justified via a 1‑page TEP.

### Push Readiness SOP (codex-4 default)

1. **Run the checklist** before publishing or requesting merge:
   ```bash
   python3 -m tools.agent.push_ready --require-test tests/<receipt-or-test>.py
   ```
   - Add `--require-receipt <path>` for receipts a reviewer must see (e.g., `_report/health/plan-lattice/<date>.json`).
   - `--allow-branch <name>` covers exceptional branches that should still be eligible.
2. **Interpret the JSON:** the command emits structured results for audit logs (`ready: true/false`, plus named checks). Capture the output in `_report/usage/push-ready/` alongside the plan executing the work.
3. **Reconcile failures:**
   - `git_clean=false` → commit/stash work or explain the deviation in a receipt before continuing.
   - `branch_match=false` → switch to `main` or an `agent/<id>/...` branch.
   - `claims_clear=false` → close or hand off active claims in `_bus/claims/`.
   - `tests_exist=false` / `receipts_exist=false` → add the missing artifacts and re-run.
4. **Log the run** by attaching both the command output and any follow-up receipts to the active plan so reviewers (and automation) inherit the same proof trail.

This SOP keeps push decisions deterministic, repeatable, and auditable; treat it as a pre-flight step for every merge.

## Backlog discipline
- **Capture ideas immediately.** The moment an actionable concept appears, log it in `docs/ideas/` (`teof ideas mark <slug> --status draft`) so its layer/systemic intent is recorded. Promote to a plan only after triage confirms scope and ownership.
- **Store ranking metadata.** Every plan must include:
  - `priority` (0 = highest, increasing numbers for later work)
  - `layer` (L0–L6 from the constitutional stack)
  - `systemic_scale` (1–10, see [`docs/foundation/systemic-scale.md`](docs/foundation/systemic-scale.md))
  - `impact_score` (relative leverage)
- **Promote ideas with receipts.** When a plan is opened, run `teof ideas promote <id> --plan-id <plan>` so the originating idea links to `_plans/<plan_id>.plan.json` and downstream receipts reference the same coordinates.
- **Update assignments and claims.** Once a plan exists, create or refresh the bus claim (`python -m tools.agent.bus_claim claim --task <task> --plan <plan_id>`) so coordination surfaces know who owns the promoted idea; release or reassign via `tools.agent.task_sync` as work progresses.
- **Optional shorthand.** When talking out loud, you can abbreviate the coordinate (e.g. `S6:L4` for Truth/Architecture), but keep the explicit numeric fields in plans and memory so automation can parse them.
- **Use the planner CLI** to enforce the schema; `planner list` sorts by these fields so the highest leverage work stays obvious. `planner new --queue-ref queue/<id>.md` auto-populates systemic/layer coordinates from the queue entry and fails fast when metadata drifts. Run `python3 -m tools.planner.queue_scan --fail-on-warning` before consensus to emit a receipt if mismatches remain.
- Run `python -m tools.planner.backlog_summary` for a quick status snapshot (counts + top pending plans by priority).
- Use `python -m tools.planner.missing_receipts` to list queued/in-progress plans that still lack top-level receipts.
- **Log the run** (`teof memory doctor`, `teof memory timeline`) so future sessions understand why the plan exists and where it ranks.

---

## Top-layer adoption blueprint

TEOF can sit at a platform’s highest policy layer when three strands stay intact:

- **Observable value:** systemic coordinates + VDP receipts make volatile claims auditable (timestamp + source) and batch refinement proves automation runs the same playbook as humans. Market it as “fewer incidents, faster attestations.”
- **Shared governance:** keep the constitution append-only (`governance/anchors.json`) and invite the host’s stewards into Meta‑TEP + anchors flow so rule changes are transparent, receipt-backed, and reversible.
- **Clear rollout:**
  1. **Pilot** a high-risk surface (e.g., volatile data output) with `scripts/ci/check_vdp.py`, attach plan receipts, and publish the audit bundle.
  2. **Harden** proof: sign receipts, mirror `_report/**` into tamper-evident storage, and script escalations when automation must pause for humans.
  3. **Integrate** platform safety: map existing redlines (content policy, privacy) to their systemic axes, encode matching guards, and prove coverage via `_plans/*` + anchors events before elevating TEOF to the top layer.

This keeps Observation → Ethics → Self-repair coherent while giving companies the confidence levers—deterministic audits, shared stewardship, incremental adoption—to promote TEOF without diluting the constitution.

---

## Architecture Gate (before writing code)
- Place new work per `docs/architecture.md` (extensions / experimental / archive / docs / scripts / governance).
- Prototypes start in `experimental/` with a short promotion plan in the PR.
- Kernel code **MUST NOT** import from `experimental/` or `archive/` (the import policy guard enforces this).
- If a new top-level seems required, open a 1‑page TEP in `rfcs/` (purpose, contract, alternatives, rollback).
- Continuously benchmark high-reliability ecosystems (SRE playbooks, regulated automation, audited release trains) and adapt the proven guardrails so TEOF’s workflow evolves with the wider industry.

### Layer hierarchy (L0–L6)

| Layer | Name         | Purpose                                        |
|-------|--------------|------------------------------------------------|
| L0    | Observation  | Raw perception, receipts, measurements         |
| L1    | Principles   | Stable rules distilled from observation        |
| L2    | Objectives   | Goals that serve the principles                |
| L3    | Properties   | System traits required to meet objectives      |
| L4    | Architecture | Concrete structures that express the properties|
| L5    | Workflow     | Human/agent procedures that maintain the architecture |
| L6    | Automation   | Executable systems that uphold the workflow    |

L1 Principles (P1–P7) apply to every downstream layer, and the systemic axis
(`docs/foundation/systemic-scale.md`) supplies the Unity → Meaning order the
architecture must respect. Tag every plan, receipt, or artifact with both
coordinates (e.g., `S6:L4`) so systemic priorities and structural layers stay in
view.

---

## Non‑negotiables (apply to every change)
- **Minimalism:** keep complexity the same or lower for equal capability. If complexity increases, justify in one sentence in the PR body.
- **Single Source of Truth:** immutable baselines live under `capsule/<version>/` and are covered by `capsule/<version>/hashes.json`. `capsule/current` stays a symlink to the active version; treat it as the canonical pointer.
- **Determinism:** commands run reproducibly on a clean machine (no hidden state, same output paths).
- **Append-Only Governance:** `governance/anchors.json` is append-only; releases map to a baseline with a `prev_content_hash`.
- **Observation Discipline:** claims follow [VDP](foundation/alignment-protocol/TAP.md#volatile-data-protocol-vdp-and-ogs-requirements); reasoning can be scored with [OGS](OGS-spec.md). The `check_vdp` guard and golden fixtures keep receipts citational; use **N/A** when not applicable.
- **Fractal accountability:** `scripts/ci/check_fractal_conformance.py` must pass (counts must stay at or below `docs/fractal/baseline.json`, trending toward zero) before automation can promote work downstream.
- **Retro advisories:** the same guard writes `_report/fractal/advisories/latest.json`; convert any entries with your plan ID or path into queue backfill items before starting new work.
- **Defensive exception logging:** when urgent action must precede planning, surface the observation to governance immediately and backfill receipts as soon as practicable so the deviation remains auditable.
- **Stable Interfaces:** prefer console scripts (`teof-validate`, `teof-ensemble`) or `python -m …` over deep file paths.
- **Quickstart Guard:** CI runs the canonical smoke test (`scripts/ci/quickstart_smoke.sh`) so the snippet in docs stays runnable; any divergence fails guardrails.

---

## DNA Recursion (self‑improvement of the rules)
**Goal:** continuously refine our own architecture, workflow, and promotion policy without bloating the kernel.

**When to trigger**
- Repeated friction (same exception to rules ≥2 times)  
- Structural drift (files don’t fit placement rules)  
- Material change in scope/audience (new app/repo boundary)  
- Periodic maintenance (optional cadence)

**How (Meta‑TEP)**
1) Open `rfcs/TEP-dna-<short-topic>.md` describing: **Problem**, **Proposal**, **Alternatives**, **Impact**, **Rollback**.  
2) Land the doc change (`docs/architecture.md`, `docs/workflow.md`, `docs/promotion-policy.md`).  
3) Append a governance event (type=`dna-change`) in `governance/anchors.json` (optionally include a hash of the updated DNA docs).  
4) Add a one‑line note to `CHANGELOG.md` under “Docs/DNA”.

**Non‑negotiables for DNA changes**
- **Minimalism:** rule count stays flat or goes down  
- **Stability:** no breaking of public import surface (`extensions.*`)  
- **Provenance:** every DNA change is anchored (append‑only)  
- **CI discipline:** no new CI rules unless they protect the kernel (import policy remains the only hard guard)

---

## PR Checklist (the only 6 checks that must pass)
- [ ] **Objective line (one sentence)**  
  `Class=<Core|Trunk|Branch|Leaf>; Why=…; MinimalStep=…; Direction=…`

- [ ] **Placement & import guard**  
  Files are placed per `docs/architecture.md`. Run `bash scripts/policy_checks.sh` (or let CI run it) — **no** `extensions/` imports from `experimental/` or `archive/`.

- [ ] **Baseline gate**  
  If critical/immutable files changed: put them under `capsule/<version>/`, run `bash scripts/freeze.sh`, and ensure CI verify passes (hashes, anchors, no junk files).

- [ ] **Evidence/goldens**  
  If validator/evaluator logic or reasoning rules changed: update `docs/examples/**/expected/` goldens and include a brief rationale. Systemic readiness commands must run and produce artifacts.

- [ ] **Minimal surface**  
  Provide the smallest runnable demo or doc snippet (CLI invocation + output path) that shows the change; else **N/A**.

- [ ] **Changelog touch**  
  If behavior or immutable scope changed, update `CHANGELOG.md`. (Tie to anchors event when applicable.)

> If this PR edits the DNA (architecture/workflow/promotion policy), also follow **DNA Recursion** above.

---

## Lean release block (only when tagging)
1) Ensure `capsule/current` points to `vX.Y` and `hashes.json` is final (`bash scripts/freeze.sh`).  
2) Append an anchors event in `governance/anchors.json` (includes `prev_content_hash`, `{tag, baseline}`; if DNA changed, include its hash).  
3) Update `CHANGELOG.md` with date and bullets.  
4) Tag and archive:  
   ```bash
   git tag -a vX.Y.Z -m "…"
   git push origin vX.Y.Z
   # optional: zip capsule for distribution
   (cd capsule && zip -r "../artifacts/teof-vX.Y.Z.zip" "vX.Y")
   ```
5) Publish the release with the zip (optional).
6) Update capsule status markers: adjust `capsule/README.md` and add/update `capsule/vX.Y/status.md` when promoting a new baseline so downstream tooling sees the active release.  
7) Review `docs/maintenance/capsule-cadence.md` and capture receipts (`_report/manager/…`) before tagging a release.  

---

## Working order (day‑to‑day)

## Consensus review cadence

- **Daily (async):** rotate through engineers to run `python -m tools.consensus.ledger --limit 5` and `python -m tools.consensus.dashboard --format table --since <24h>`; log `bus_event --consensus-decision <id>` for any decisions touched and stash the output under `_report/agent/<id>/consensus/`.
- **Weekly (manager):** the current manager runs both CLIs for the trailing week, appends a receipt via `python -m tools.consensus.receipts --decision WEEKLY-<ISO>` and shares a short summary in `manager-report.jsonl`.
- **Weekly telemetry:** roll up preflight usage with `python -m tools.usage.preflight_summary --window-hours 168 --output _report/usage/preflight/preflight-summary-<ISO>.json` and link it in `manager-report.jsonl` so we can see how often the heavy lane triggers.
- **Escalation:** if a decision lacks receipts after a daily sweep, post `bus_message --type request --meta escalation=consensus` tagging the owner and record the follow-up in the next sweep.
- **Receipts:** daily sweep logs live under `_report/agent/<id>/consensus/`; weekly summaries go to `_report/manager/` (linkable from manager reports) so audits and automation confirm cadence compliance.

1) Confirm placement vs Architecture; fix anchors ↔ baseline as needed.  
2) Make CI **verify** green (import policy + brief shape checks).  
3) If reasoning changed, wire evaluator + update goldens.  
4) Expose a minimal surface (one command → artifacts).  
5) Log the run in the memory layer (`teof memory doctor` before closing the session; store capsule under `memory/runs/<id>/` and promote durable facts via the helper API).  
6) Tag & ship when ready.

> **Placement note:** this file lives **outside** the capsule to avoid baseline churn. After it stabilizes (several cycles without edits), move it into `capsule/current/` and re‑freeze hashes.

## Batch refinement mode (trusted automation)

Use this lane when trusted automation can land several low-risk refinements without a human pausing the loop. It keeps autonomy high while preserving receipts and early-warning signals.

- **Scope:** docs, hygiene tooling, guardrails already covered by tests, coordination helpers, or refactors that stay inside existing policy. Any DNA, governance, ethics, capsule, or manager directive change still pauses for explicit human acknowledgement.
- **Checklist before the batch starts:**
  - Plan enumerates the intended refinements and cites a low-risk scope.
  - Operator preset receipt from `python -m tools.agent.session_brief --task <id> --preset operator` is fresh (warn statuses resolved or intentionally accepted).
- **During the batch:**
  - Prefer the helper: `python -m tools.agent.batch_refinement --task <id> [--agent <id>]` (optionally pass `--pytest-args ...`) to run tests, receipts hygiene, and capture the operator preset receipt in one shot. The helper writes a batch log under `_report/usage/batch-refinement/` for audit.
  - Run full tests for the touched surfaces; if any command returns non-zero, stop immediately and escalate on `manager-report` with `--meta escalation=batch`.
  - If uncertainty about policy or ethics surfaces, pause and post on the bus before continuing.
- **Batch handoff:**
  1. Run `python -m tools.agent.receipts_hygiene --quiet` (or the equivalent helper) to refresh `_report/usage/receipts-hygiene-summary.json`.
  2. Generate a new operator preset receipt referencing the hygiene summary (`session_brief` now includes this check).
  3. Post a single bus summary pointing to the operator preset receipt and the hygiene summary path.
- **Automatic escalations:** the session must stop and ping `manager-report` when:
  - `receipts-hygiene-summary.json` reports any `plans_missing_receipts > 0` or the CLI fails to run.
  - Tests fail, guardrails reject a change, or planner validation drops to `warn/fail`.
  - Work drifts into DNA/governance scope or requires policy interpretation beyond the documented checklist.

These rules let trusted automation keep shipping routine improvements while giving humans a single artifact (the operator preset receipt) to audit the batch.

## Fitness Lens (tools & CI)
- **Preflight is invariants-only.** Tools that don’t measurably improve systemic coverage remain **opt-in**.
- Use `docs/policy/fitness-lens.md` to justify any blocking check with receipts + sunset.
