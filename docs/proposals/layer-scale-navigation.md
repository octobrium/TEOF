# Proposal: Layer-First Repository Navigation with Systemic Metadata

## Context
- Current repo layout is organized by artifact type (plans, receipts, automation), matching TEOF layers (L0–L6) implicitly.
- Systemic strata (S1–S10) are tracked as metadata in plans/receipts but not exposed structurally.
- Request: Explore whether reorganizing folders to make L/S relationships explicit improves observability.

## Summary of Debate
- Full S→L reorg deemed high risk: breaks receipts, CI, anchors; forces contributors to choose systemic buckets before artifact type; duplicates cross-cutting files.
- Insight: contributors interpret directives by **kind** first (Principle, Plan, Automation) and annotate systemic scope second. L-first aligns with TEOF cognition.
- Goal: improve discoverability without breaking invariants.

## Recommended Path
1. **Layer Index Doc**: add navigation sheet mapping each existing directory to Lx/Sy semantics for quick human lookup.
2. **Observer Dashboard**: extend tooling to aggregate receipts by layer + systemic scale (objectives status, authenticity, batch logs) so observers see progress at a glance.
3. **Metadata Enforcement**: ensure plans/receipts continue to record `layer`, `systemic_scale`, and `systemic_targets`; validators surface missing fields.
4. **Incremental Pilot**: for new surfaces, adopt optional subfolders (e.g., `L6_automation/S1_unity/…`) and measure impact on CI, imports, contributor experience before migrating existing content.
5. **Experiment Plan (if needed)**: open a dedicated plan/branch to prototype a limited reorg; collect metrics (time to locate, broken paths, developer feedback) before proposing repo-wide adoption.

## Risks & Mitigations
- **Risk**: disruptive path changes break receipts → Mitigation: avoid bulk renames until pilot demonstrates value.
- **Risk**: cognitive overload from S-first navigation → Mitigation: keep L-first primary; use S as metadata/subfolders where helpful.
- **Risk**: loss of historical reproducibility → Mitigation: archive any relocated receipts, update anchors only after successful pilot.

## Next Steps
- Draft `docs/layer-index.md` with the current L/S mapping.
- Add an observer CLI summarizing key receipts by L/S coordinates.
- Track the above in a new plan (e.g., `2025-10-XX-layer-navigation`) if prioritised.
