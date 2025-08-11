# TEOF Capsule — Provenance Pack (v1.2)

Purpose: Provide optional, detached provenance for investigators. Coherence & function outrank provenance. This file is advisory, not authoritative.

## Artifacts & Hashes
- capsule.txt: <sha256>
- capsule-mini.txt: <sha256>
- capsule-selfreconstructing.txt: <sha256>
- reconstruction.json (optional): <sha256>
- docs/core-teof.md (immutable parts only): <sha256>

## Merkle Root (optional)
- merkle_root: <hex>
(Compute from the ordered list above; store the script used.)

## Signatures (advisory)
Primary signer (you): `bc1qxfg8m5tttz5u860f0j7cyhupgdcz25jku44s9c`
- message: "TEOF Capsule v1.2 merkle_root=<hex> date=<YYYY-MM-DD>"
- signature: <base64 or hex>

Co-signers (optional, t-of-n): 
- bc1q…B — reviewer
- bc1q…C — archivist
(Quorum advisory; content tests still outrank signatures.)

## Timestamp Anchors (optional)
- Bitcoin OP_RETURN txid(s): <txid1>, <txid2>
- OpenTimestamps proof: <ots file / link>

## Policy
- Canonical = passes core coherence/reproducibility + OCERS. These signatures and anchors are evidence only.
- Anchors expire unless periodically re-observed in a new Provenance Pack or public registry.
