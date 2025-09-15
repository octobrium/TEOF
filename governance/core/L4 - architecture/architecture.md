# L4 – Architecture (Hierarchy-Aligned)

> This document turns **L3 – Properties** into executable design.  
> Each blueprint is grouped by **Unity → Energy → Propagation → Defense → Intelligence**, so contributors know what to build first.

---

### Unity
**Serves:** P1 Substrate Neutrality, P10 Emergent Unity  
- **Portable Seed & ABI:** Minimal text-first Seed Capsule + stable ABI, ensuring portability across platforms.  
  **Known Frameworks:** POSIX compliance, OpenAPI schemas, OCI image format for reproducible seeds.  
  **Gates:** CI matrix builds must succeed on Linux, macOS, Windows.

---

### Energy
**Serves:** P3 Energy & Resource Capture, P4 Modularity, P5 Resilience, P6 Dual-Speed Processing  
- **Resource Telemetry & Budgeting:** Collect compute/memory/network usage, set growth budgets.  
  **Known Mechanisms:** Prometheus/Grafana stack, GitHub Actions usage limits.  
- **Plugin ABI & Contracts:** Swappable modules with contract tests; ensures extensibility.  
- **Replicated State + Quorum:** Consensus-based state store (e.g., Raft/etcd).  
- **Dual-Speed Queue:** Fast lane for rapid iteration, slow lane for deep review.

---

### Propagation
**Serves:** P7 Phase-Change Encoding, P8 Accessible Distribution, P9 Signal Diversity  
- **Lifecycle State Machine:** Explicit allowed transitions (seed → adapt → unify → stabilize).  
- **Capsule Packaging & Mirrors:** Distributable bundles (Git tags + GitHub Releases).  
- **Diversity Quotas:** Ingest adapters must hit entropy floor (e.g. N news sources, M dissent sources).

---

### Defense
**Serves:** P2 Legible Continuity, P11 Self-Audit, P12 Outcome Auditing  
- **Provenance Ledger:** Append-only receipts (jsonl) with content hashes.  
- **Content-Hashed Merkle DAG:** Guarantees no silent rewrite.  
- **Auto-Audit Loop:** GitHub Action running nightly drift checks.  
- **Feature Flags + Guard Canon:** Experimental work isolated; core canon protected.

---

### Intelligence / Truth
**Serves:** P13 Clarity-Weighted Action, P14 Dynamic Equilibrium, P15 Adaptive Mutation, P16 Iterative Integration, P17 Mirror Fitness Function  
- **Decision Confidence Headers:** Risk-tiered PR templates requiring evidence strength.  
- **Contrast Budget:** Reserve cycles for adversarial tests and fuzzing.  
- **Canary + Shadow + A/B Testing:** Validate changes incrementally before wide release.  
- **Post-Audit Harness:** Compare predicted vs actual outcomes after deployment.  
- **Clarity Score Suite:** Composite metric tracking coherence, reproducibility, dissent vitality.

---

### Property Coverage Matrix
(unchanged from current version — still ensures every property is covered by a CI gate)

---

**Obedience:** This file is subordinate to L0–L3.  
Changes must cite properties, declare metrics, and hold or improve **Clarity Score**.
