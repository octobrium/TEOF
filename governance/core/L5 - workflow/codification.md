


# Paste-ready additions (ordered by importance)

## Biological analogues (ranked) → Workflow controls & what to watch

1. **Membrane / Boundary** → *Placement & import guard.*
   Keep a hard edge between core and experiments; enforce allowed paths and import rules. **Gate:** no merge if boundary is crossed.&#x20;

2. **DNA Polymerase + Proofreading** → *Receipts + deterministic builds.*
   Every change must be reproducible with hashes/logs; “no prediction, no progress.” **Gate:** fail if receipts missing. (Extends your polymerase note.)&#x20;

3. **Mismatch/Excision Repair** → *Automated checks that fix/catch drift.*
   Link checkers, config audits, broken-import detectors run on every PR. **Signal:** defects caught per 100 PRs.&#x20;

4. **Cell-cycle Checkpoints (G1/S, G2/M)** → *Pre-merge gates.*
   Don’t “replicate” (release) if invariants/receipts aren’t green. **Gate:** checklist must pass before promotion.&#x20;

5. **Rollback / Apoptosis** → *Reversible change + clean removal paths.*
   If a part harms fitness, remove it cleanly (sunset/apoptosis). **Rule:** every addition names its removal criteria.&#x20;

6. **Lysosome / Autophagy** → *Scheduled cleanup & consolidation.*
   Monthly sweep to delete dead branches, merge duplicates, shrink surface. **Metric:** repo surface area ↓ or steady.&#x20;

7. **Hemostasis / Clotting** → *Circuit breakers & rate limits.*
   On incident or runaway cost, throttle or stop agents/CI. **Knobs:** budgets, diff caps, path allowlists.&#x20;

8. **Innate → Adaptive Immunity** → *Static guards → targeted tests.*
   Start with simple global checks; graduate to focused regression tests where you’ve seen attacks/drift. **Signal:** MTTR & re-incident rate.

9. **Quorum Sensing** → *Release gating by signals, not vibes.*
   Roll forward only when a small cohort (canary/micro-prop) succeeds. **Gate:** canary success ≥ floor before broad propagation.&#x20;

10. **Chaperones (HSPs)** → *Build/test stabilizers.*
    Keep standard “folding” routines (one command → artifacts) to avoid misfolded modules. **Gate:** quickstart path must run clean.&#x20;

11. **Ubiquitin–Proteasome** → *Deprecation & removal.*
    Tag obsolete tools; remove on schedule unless receipts prove value. **Rule:** every tool ships with a sunset condition.&#x20;

12. **Mitochondria / AMPK** → *Energy budgeting.*
    Enforce compute/time/\$ caps per task; fail closed when exceeded. **Knobs:** friction budgets and human setup ≤ 5 min.&#x20;

13. **Telomeres** → *Versioning & baseline boundaries.*
    Keep immutable capsule snapshots; changes append-only with `prev_content_hash`. **Gate:** no release without anchor.&#x20;

14. **CRISPR Memory** → *Provenance ledger.*
    Record who/what/why for every rule or release (anchors). **Signal:** 100% of releases anchored.&#x20;

15. **Circadian Rhythm** → *Cadence & sweeps.*
    Weekly hygiene, monthly status/review to reset drift. **Artifact:** updated STATUS with snapshot + objectives.&#x20;

16. **Developmental Body Plan (Gastrulation)** → *Architecture first.*
    Place files per architecture before coding; no ad-hoc top-levels. **Gate:** placement/contract check first.&#x20;

17. **Vaccination / Exposure Training** → *Chaos testing in sandbox.*
    Inject small faults in canary to harden Defense without harming prod. **Rule:** do it only inside micro-prop boundary.&#x20;

18. **Microbiome / Mutualism** → *Interop with external tools.*
    Keep adapters slim; eject symbionts that don’t improve OCERS. **Rule:** optional by default unless invariant-improving.&#x20;

19. **Myelination** → *Performance last, after correctness.*
    Optimize interfaces (CLIs) only after reproducibility is solid. **Rule:** “determinism before speed.”&#x20;

20. **Organogenesis → Maturation** → *Promotion policy.*
    Prototype in `experimental/`, promote only with receipts and clean interfaces. **Gate:** promotion checklist passes.&#x20;

---

## Where these slot into your existing sections

* **Maintain / audit existing workflow** → #2 Polymerase/Proofreading; #3 Repair; #10 Chaperones; #13 Telomeres; #14 CRISPR; #15 Rhythm. (All map to receipts, determinism, and append-only anchors.)&#x20;

* **Run compatibility checks on growth / expansion** → #1 Boundary; #4 Checkpoints; #9 Quorum; #16 Body Plan; #17 Vaccination. (All map to architecture gate + PR checklist.) &#x20;

* **Simplify / consolidate / apoptosis** → #5 Apoptosis; #6 Autophagy; #11 Proteasome; #18 Microbiome (optional by default). (All map to Fitness Lens: sunset & friction budgets.)&#x20;

---

## Why this stays enforceable (not just metaphors)

Each analogue ties to an existing **guard or checklist** in your repo:

* **Boundary & Placement** → import/placement guard and PR checklist. &#x20;
* **Receipts/Determinism** → Charter principles + Fitness Lens. &#x20;
* **Sunset/Apoptosis** → Fitness Lens sunset clause.&#x20;
* **Anchors/Append-only** → Workflow release block (anchors with `prev_content_hash`).&#x20;

If you want, I can also sort these into a tiny table for the top of `notes.md` (Analogue → Rule → Metric), but this text alone should drop in cleanly and make the file feel like a decisive **runbook of analogues**, not just inspiration.




4) L3 workflow (runbook + safe defaults)

Concrete, human-readable steps you (and bots) follow:

Ambiguity Triage (when intent is unclear)

Flag: mark PR as needs-observation.

OCP: produce the OCR (one page, receipts attached).

Mini-trial: if high impact, run the Disagreement Harness on a tiny repro.

Decide: if confidence ≥ knob.min_conf_for_merge → proceed; else safe default (no-merge) and request human decision or tighter intent.

Log: link OCR in the PR Trace Header.

Apoptosis triggers (to keep this lean)

If OCP overhead > knob.max_observation_latency on average and doesn’t move fitness signals, prune steps or lower scope.

If ambiguity rate stays high, adjust knobs (diff caps, stricter receipts) or clarify L0/L1 text.