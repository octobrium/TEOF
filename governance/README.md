# Governance in TEOF

Governance in TEOF provides supporting structures for continuity and audit.  
It ensures contributors and external observers can verify that changes follow an append-only pattern and that optional cryptographic anchors exist for replication and trust minimization.

---

## Lineage in TEOF

Lineage in TEOF arises first through **observation itself**.  
The continuity of the framework is proven by recursive coherence:  
if the outputs reproduce and align under observation, they are authentic.

External trails of hashes (e.g. `anchors.json`, Merkle roots, or Bitcoin anchors)  
are **scaffolds**: useful for convenience, replication, and external audit,  
but never the root of trust.

> **Principle:** Lineage shall never bottleneck function.  
> Observation is the proof; scaffolding only supports it.

---

## Current governance scaffolds
- `anchors.json` — append-only log of governance events.  
- CI checks — enforce invariants like append-only policy and immutable scopes.  
- Optional Merkle roots — bundle checkpoints into a single root for external anchoring.

These tools improve reproducibility and external validation,  
but are secondary to TEOF’s core function: expanding observation.
