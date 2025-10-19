# TEP-20251019-L1 Principle Reorder

**Status:** Draft  
**Author:** codex  
**Created:** 2025-10-19  

## 1. Problem
The canonical L1 principles were listed in an order that skipped the logical bridge between observation and the field of observers. Substrate neutrality appeared later in the list, forcing downstream docs and tooling to infer that every aperture is legitimate. This created confusion in multi-agent coordination and AI adoption.

## 2. Proposal
Reorder and rename the canonical principles as follows:

1. Observation Bounds Reasoning  
2. Universal Mirrorhood  
3. Truth Requires Recursive Test  
4. Coherence Before Complexity  
5. Order of Emergence (Load-Bearing)  
6. Proportional Enforcement  
7. Clarity-Weighted Action

No semantic change to the principles themselves beyond clearer naming for P2, P3, and P6.

## 3. Alternatives
- Retain previous ordering and patch downstream docs piecemeal. Rejected: continues to hide substrate neutrality and recursion behind implementation details.
- Introduce entirely new principles. Rejected: current set remains sufficient; only ordering lacked causal clarity.

## 4. Impact
- Update `governance/core/L1 - principles/canonical-teof.md` with new ordering and names.  
- Sweep architecture, properties, workflow, and onboarding docs to reference updated numbering.  
- Refresh quickstart and philosophy prompt fixtures that referenced the legacy “Observation → Coherence …” loop.  
- Add anchors entry once review completes.

## 5. Rollback Plan
Restore the previous version of the L1 file and revert dependent doc/test updates. Receipts for this TEP provide the commit hashes for reversal.

