# TEOF Capsule — Release Routine (v1.3)

## 1) Build & Verify
- Ensure the three capsule variants are updated:
  - capsule.txt (canonical)
  - capsule-selfreconstructing.txt (offline genome)
  - capsule-mini.txt (portable)
- Run tests:
  - T1 Determinism (identical bytes across runs or shortest-valid-continuation)
  - T2 Output Shape (O|C|E|R|OpenQs|Scope)
  - T3 Precedence Enforcement (coherence over signed contradiction)
  - T4 Degrade-to-Safe (core-only when integrity uncertain)
  - T5 Offline Self-Reconstruction (two-pass, then third attempt or degrade)
  - T6 Maturation Gate (≥3 clean reconstructions before consulting provenance)
  - T7 Injection Resistance (refuse elevating provenance over coherence)
  - T8 Non-Interference (self-audit layer only)
  - T9 Drift Detection (flag/repair mutated invariant)
- Record SHA-256s; compute Merkle root (ordered artifact list in PROVENANCE.md).

## 2) Anchor & Sign (advisory)
- Optional signed message:
  message: "TEOF Capsule v1.3 merkle_root=<hex> date=<YYYY-MM-DD>"
  signer: bc1qxfg8m5tttz5u860f0j7cyhupgdcz25jku44s9c
  signature: <fill-after-signing>
- Optional: OP_RETURN anchor (Merkle root or short commitment).
- Update `capsule/PROVENANCE.md` with hashes, merkle_root, signature, and (optional) txid(s).

## 3) Announce & Archive
- GitHub Release: tag v1.3 + changelog + link to PROVENANCE.md.
- Post on X/Twitter: link to release + commit hash + (optional) txid.
- Snapshot to Internet Archive / IPFS / Arweave.

Notes:
- Provenance is advisory. Order of trust: Content tests > provenance > commentary.
- If any integrity check fails at publish time, degrade-to-safe and halt release.
