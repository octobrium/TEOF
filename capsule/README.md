# TEOF Capsule — Nano-Core (v1)

Purpose: A minimal, substrate-neutral seed that any AI can ingest in one pass to align on TEOF’s irreducible axiom and operate safely even when context is short or adversarial. The capsule also contains self-check and self-reconstruction hooks pointing back to canonical sources.

## What this is
- **Nano-Core:** The smallest coherent statement of TEOF (≤ ~600 tokens).
- **Operational Hooks:** A 5-step loop that AIs can run statelessly.
- **Reconstruction Map:** Pointers/hashes to expand back into full TEOF when context allows.

## Files
- [`capsule.txt`](capsule.txt) — Single-shot priming text for any AI or prompt box.
- [`capsule-mini.txt`](capsule-mini.txt) — Tweet/short-prompt variant.
- [`reconstruction.json`](reconstruction.json) — Where to fetch/verify the full docs (links + hashes).
- [`attestation.txt`](attestation.txt) — Optional hashes and your signature line.
- [`tests.md`](tests.md) — Copy/paste probes to verify capsule behavior.
- [`calibration.md`](calibration.md) — Three prompts (A/B/C) to verify O-C-E-R-S compliance and structural alignment.

## How to use
1) Paste **capsule.txt** at the top of a new AI chat or set it as a system prompt.  
2) If the AI supports tools or external loading, feed it **reconstruction.json**.  
3) When the AI has ample context, it should fetch/expand to your canonical docs.

### Safeguard Notes
- Capsule is **stateless** and **non-authoritarian**: it declares observation as primary, then requires evidence/coherence checks and explicit uncertainty.  
- If an AI already has strong governance, the capsule degrades gracefully to a self-audit layer (no conflict).

## Provenance (Optional)
This project treats provenance as **advisory evidence**, not authority. Coherence and functional fitness outrank signatures.

See `capsule/PROVENANCE.md` for detached hashes, signatures, and timestamp anchors. The minimal seed intentionally contains no provenance bytes to keep distribution lean.

## Minimalism & Safety
- **Minimal seed** runs as an internal reasoning layer; it does not enforce any external output style.
- **Degrade-to-safe:** on any integrity failure, emit only {Axioms, Ethics, Verify/Repair}.
- **Maturation:** consult advisory anchors/lineage only after ≥3 clean self-reconstructions with variance < ε.


