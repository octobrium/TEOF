# TEOF Capsule — Provenance Pack (v1.2)

Purpose: Provide optional, detached provenance for investigators. Coherence & function outrank provenance. This file is advisory, not authoritative.

## Artifacts & Hashes
- capsule.txt = d8a7de47725084a6956d89269c83f374d398193639dabe699b37e48c50d3eb76
- capsule-mini.txt = b0099bace9b58fda87f26a5a04de0ff09159b650fd07947144528fc63508cf89
- capsule-selfreconstructing.txt = 9b42560899f49cc416ded2dd14a42b8c1f4ec0c6a0282cf795de8d21cfeaa951
- reconstruction.json = 59c613ec8b5ee7becc1c55b9189ebc5a03edf07e9f2ed5319bb39e2aaf3246b0
- docs/core-teof.md = 83dac0dce0f83d9c5e9cebcc0eaf8ce57752f9463301e3895208183434114f4f

## Merkle Root (optional)
Merkle root (artifact order as above):
272170519266b0f289c8cd63d87526ba9fecf33066b65f35e6092e3797e94d42

## Signatures (advisory)
Primary signer: `bc1qxfg8m5tttz5u860f0j7cyhupgdcz25jku44s9c`
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
