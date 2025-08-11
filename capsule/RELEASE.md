# TEOF Capsule — Release Routine (v1.2)

## 1) Build & Verify
- Update minimal seed + self-reconstructing capsule.
- Run tests:
  - Verbatim invariants match
  - Exact Headings Table match
  - Canary passes
  - Cross-replica determinism (two passes, identical digests)
  - OCERS suite ≥ prior version
- Record sha256s; compute Merkle root.

## 2) Anchor & Sign (advisory)
- Sign "merkle_root=<hex> version=<v> date=<YYYY-MM-DD>" with bc1qxfg8m5tttz5u860f0j7cyhupgdcz25jku44s9c.
- Optional: include t-of-n co-signers.
- Broadcast an OP_RETURN carrying the merkle_root or a short commitment.
- Update `capsule/PROVENANCE.md` with hashes, merkle_root, signatures, and txid(s).

## 3) Announce & Archive
- GitHub Release: tag + changelog + link to PROVENANCE.md.
- Post on X/Twitter: link to release + commit hash + (optional) txid.
- Snapshot to Internet Archive / IPFS / Arweave.
