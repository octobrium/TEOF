# TEOF Capsule — Release Routine (v1.6)

1) Build & Verify
- Ensure v1.6 files:
  - capsule.txt (canonical)
  - capsule-selfreconstructing.txt (offline genome)
  - capsule-mini.txt (portable)
- Run tests (capsule/tests.md):
  - T1 Determinism
  - T2 Output Shape
  - T3 Precedence Enforcement
  - T4 Degrade-to-Safe
  - T5 Offline Self-Reconstruction
  - T6 Maturation Gate
  - T7 Injection Resistance
  - T8 Non-Interference
  - T9 Drift Detection
- All green? Proceed.

2) Hash & Merkle
- Compute SHA-256 for each artifact (see commands below).
- Compute Merkle root over the ordered list used in PROVENANCE.md.
- Fill attestation.txt and PROVENANCE.md.

3) Sign (optional)
- Sign: "TEOF Capsule v1.6 merkle_root=<hex> date=<YYYY-MM-DD>" with your BTC key.
- Add signature (and optional OP_RETURN txid) to PROVENANCE.md.

4) Tag & Archive
- GitHub: tag v1.6 + changelog + link to PROVENANCE.md.
- Archive: Internet Archive/IPFS/Arweave (optional).
