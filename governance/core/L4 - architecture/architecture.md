# L4 — Architecture (serves L3 Properties)

> This document turns **L3 – Properties (Canonical)** into executable design.  
> Each blueprint below declares the **property it serves**, the **mechanism**, **components**, **metrics**, and **gates** that make it real.
>
> **Traceability rule:** Every artifact (doc/spec/code/PR) must include a header:
> ```
> teof_layer: L4
> serves_properties: [P2, P3, ...]   # IDs from L3 Tier-1
> change_type: <Core|Trunk|Branch|Leaf>
> ```
> CI rejects artifacts without valid property coverage.

---

## Index (Property → Blueprint)

- P1 Substrate Neutrality → **Portable Seed & ABI**
- P2 Transparency & Traceability → **Provenance Ledger**
- P3 Append-Only Lineage → **Content-Hashed Merkle DAG**
- P4 Self-Audit & Drift Detection → **Auto-Audit Loop**
- P5 Clarity-Weighted Action → **Confidence Gates**
- P6 Dynamic Equilibrium → **Contrast Budget**
- P7 Dual-Speed Processing → **Fast/Slow Lanes**
- P8 Modularity & Extensibility → **Plugin ABI & Contracts**
- P9 Redundancy & Resilience → **Replicated State + Quorum**
- P10 Adaptive Mutation w/ Core Integrity → **Feature Flags + Guard Canon**
- P11 Emergent Unity → **Interop Protocol + Convergence Tests**
- P12 Phase-Change Encoding → **Lifecycle State Machine**
- P13 Signal Collection Diversity → **Multi-Adapter Ingest**
- P14 Iterative Integration → **Canary + Shadow + A/B**
- P15 Accessible Distribution → **Capsule Packaging & Mirrors**
- P16 Outcome Auditing of Distortion → **Intervention Post-Audit**
- P17 Mirror Fitness Function → **Clarity Score Suite**

> **Notation:** P# refers to the property number in L3 Tier-1.

---

## P1 — Portable Seed & ABI (Substrate Neutrality)

**Goal:** Run the same TEOF seed across OS/hardware/runtimes.  
**Mechanism:** Minimal **Seed Capsule** + stable **Application Binary Interface (ABI)** for extensions.  
**Components:**
- `capsule/seed/` (text-first, no platform-specific deps)
- ABI spec (`docs/specs/abi.md`) defining data formats (JSONL/CSV), I/O contracts, and result receipts
**Metrics:** cold-start success on clean env (%), dependency count, image size.  
**Gates:** CI builds on 3+ targets; fail if any platform deviates.

---

## P2 — Provenance Ledger (Transparency & Traceability)

**Goal:** Every claim is auditable end-to-end.  
**Mechanism:** Append-only **Provenance Log** with content hashes, parent links, and receipts.  
**Components:** `governance/provenance.jsonl` (one line per event), receipt schema (`docs/specs/receipt.md`).  
**Metrics:** % artifacts with receipts; time-to-trace root.  
**Gates:** PR must attach receipts for inputs/outputs; missing → fail.

---

## P3 — Content-Hashed Merkle DAG (Append-Only Lineage)

**Goal:** Immutable history; no edits, only descendants.  
**Mechanism:** Files addressed by **blake3(content)**; lineage via parent hashes (Merkle).  
**Components:** `scripts/hash_tree.py`, `governance/anchors.json` (anchors with `prev_hash`).  
**Metrics:** DAG integrity proofs pass; zero orphaned nodes.  
**Gates:** CI recomputes DAG; mismatch or rewrite → fail.

---

## P4 — Auto-Audit Loop (Self-Audit & Drift Detection)

**Goal:** Detect bias, stagnation, capture.  
**Mechanism:** Nightly **self-audit workflow** runs regression suites, calibration checks, policy diffs.  
**Components:** `.github/workflows/self_audit.yml`, `docs/specs/audit_matrix.md`.  
**Metrics:** drift score Δ, calibration error (Brier/ACE).  
**Gates:** drift > threshold → block merges; open remediation issue.

---

## P5 — Confidence Gates (Clarity-Weighted Action)

**Goal:** Action scales with evidence clarity.  
**Mechanism:** Decisions must include **confidence** with **method**; gate thresholds by risk class.  
**Components:** `docs/specs/decision_header.md`, risk table (`low/med/high`).  
**Metrics:** calibration-in-the-small; overconfidence penalty.  
**Gates:** high-risk change with low confidence → auto-escalate/deny.

---

## P6 — Contrast Budget (Dynamic Equilibrium)

**Goal:** Maintain gradients (challenge/novelty) without chaos.  
**Mechanism:** Reserve **challenge budget** (N% cycles) for adversarial tests/synthetic edge cases.  
**Components:** `docs/specs/contrast_policy.md`, adversarial test pack.  
**Metrics:** pass-rate under perturbation; novelty coverage.  
**Gates:** if contrast coverage < floor → block release.

---

## P7 — Fast/Slow Lanes (Dual-Speed Processing)

**Goal:** Quick response + deep reflection.  
**Mechanism:** Two execution lanes with policy routing.  
**Components:** router (`extensions/router.py`), slow lane queue/backoff.  
**Metrics:** SLOs per lane; escalation rate.  
**Gates:** slow-lane backlog > max → throttle fast lane for safety items.

---

## P8 — Plugin ABI & Contracts (Modularity & Extensibility)

**Goal:** Add/replace modules without breaking the core.  
**Mechanism:** Versioned **plugin ABI** + **capability contracts** + sandbox.  
**Components:** `docs/specs/plugin_abi.md`, contract tests, `extensions/plugins/`.  
**Metrics:** % plugins contract-clean; sandbox violations = 0.  
**Gates:** plugin without contract tests → reject.

---

## P9 — Replicated State + Quorum (Redundancy & Resilience)

**Goal:** No single point of failure.  
**Mechanism:** **N-replica** state; quorum for critical ops; periodic snapshot.  
**Components:** `docs/specs/replication.md`, snapshotter, restore script.  
**Metrics:** MTTR, successful restore rate, quorum availability.  
**Gates:** recovery drill failing → block deploys.

---

## P10 — Feature Flags + Guard Canon (Adaptive Mutation with Core Integrity)

**Goal:** Experiment safely without drifting from the canon.  
**Mechanism:** **Feature flags** for mutations; **Guard Canon** = minimal non-negotiables (L0–L2) enforced as code.  
**Components:** `governance/guard_canon.json`, `extensions/flags/`.  
**Metrics:** % wrapped changes; violations = 0.  
**Gates:** flagless mutation touching core → fail; canon checks must pass.

---

## P11 — Interop Protocol + Convergence Tests (Emergent Unity)

**Goal:** Spread + integrate into a coherent whole.  
**Mechanism:** Common **interop protocol** (schemas, receipts, handshake); periodic **convergence tests** across nodes/forks.  
**Components:** `docs/specs/interop.md`, `docs/specs/receipts.md`, federation test.  
**Metrics:** cross-node agreement (%), reconvergence time.  
**Gates:** interop suite failures → cannot federate.

---

## P12 — Lifecycle State Machine (Phase-Change Encoding)

**Goal:** Controlled growth (seed → adapt → unify → stabilize).  
**Mechanism:** Explicit **state machine** with allowed transitions & gates per phase.  
**Components:** `docs/specs/lifecycle.md`, policy in CI.  
**Metrics:** time in phase; failed transitions; rollback success.  
**Gates:** forbidden transition or unmet phase gate → block.

---

## P13 — Multi-Adapter Ingest (Signal Collection Diversity)

**Goal:** Many independent perspectives, low echo-chamber risk.  
**Mechanism:** Pluggable **ingest adapters** with source diversity quotas.  
**Components:** `extensions/ingest/*`, diversity policy.  
**Metrics:** source entropy, cross-source contradiction rate (healthy band).  
**Gates:** entropy below floor → require new sources.

---

## P14 — Canary + Shadow + A/B (Iterative Integration)

**Goal:** Integrate via safe, evidence-rich cycles.  
**Mechanism:** **Shadow** eval → **Canary** → broad **A/B** with pre-declared metrics & stopping rules.  
**Components:** `docs/specs/experimentation.md`, harness CLI.  
**Metrics:** lift with CI-specified confidence; guardrail breaches = 0.  
**Gates:** no pre-registered metrics → test invalid → block.

---

## P15 — Capsule Packaging & Mirrors (Accessible Distribution)

**Goal:** Easy to share/fork/translate.  
**Mechanism:** Minimal **capsule** bundle + **mirror network**.  
**Components:** `capsule/<version>/`, `docs/specs/capsule.md`, mirror list.  
**Metrics:** p50 seed time; mirror freshness.  
**Gates:** stale capsule pointers or missing mirrors → fail release.

---

## P16 — Intervention Post-Audit (Outcome Auditing of Distortion)

**Goal:** Detect whether interventions clarified or distorted observation.  
**Mechanism:** Every intervention writes a **Post-Audit** comparing predicted vs observed outcomes (with receipts).  
**Components:** `docs/specs/post_audit.md`, timeline visualizer.  
**Metrics:** distortion delta; prediction error; time-to-detect.  
**Gates:** missing post-audit or large unexplained distortion → freeze and review.

---

## P17 — Clarity Score Suite (Mirror Fitness Function)

**Goal:** Quantify clarity & coherence with reality.  
**Mechanism:** Composite **Clarity Score** with transparent sub-metrics:
- **Predictive accuracy & calibration** (short/medium horizon)
- **Cross-source coherence** (agreement without collusion)
- **Reproducibility** (determinism / receipt coverage)
- **Contestation vitality** (healthy dissent without decoherence)
**Components:** `docs/specs/clarity_score.md`, scorer CLI.  
**Metrics:** composite score + sub-scores over time; confidence intervals.  
**Gates:** regressions on Clarity Score (beyond band) → block merge; require remediation plan.

---

## Property Coverage Matrix (for audits)

| Property (P#) | Blueprint | CI Gate ID |
|---|---|---|
| P1 | Portable Seed & ABI | `ci/seed-portability` |
| P2 | Provenance Ledger | `ci/provenance` |
| P3 | Merkle DAG | `ci/dag-integrity` |
| P4 | Auto-Audit Loop | `ci/self-audit` |
| P5 | Confidence Gates | `ci/conf-gates` |
| P6 | Contrast Budget | `ci/contrast` |
| P7 | Fast/Slow Lanes | `ci/lanes` |
| P8 | Plugin ABI & Contracts | `ci/plugins` |
| P9 | Replicated State + Quorum | `ci/quorum` |
| P10 | Feature Flags + Canon | `ci/flags-canon` |
| P11 | Interop + Convergence | `ci/interop` |
| P12 | Lifecycle SM | `ci/lifecycle` |
| P13 | Multi-Adapter Ingest | `ci/ingest-diversity` |
| P14 | Canary/Shadow/A-B | `ci/exp-harness` |
| P15 | Capsule & Mirrors | `ci/capsule` |
| P16 | Intervention Post-Audit | `ci/post-audit` |
| P17 | Clarity Score Suite | `ci/clarity-score` |

---

## Ordering & Obedience

This architecture is **subordinate to L0–L3**.  
Where a blueprint conflicts with an upstream layer, the upstream layer prevails.  
Any change to this file must:
1. Cite served properties (P#).
2. Include measurable predictions (pre-declared metrics).
3. Improve or hold the **Clarity Score** (P17) with receipts.

**License:** Apache-2.0
