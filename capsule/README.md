# TEOF Capsule

**Stable entrypoint:** all canonical artifacts live under [`./current/`](./current/).  
This README is versionless and does not require edits when new versions are released.

## Canonical artifacts
- [capsule.txt](./current/capsule.txt) — full capsule
- [capsule-mini.txt](./current/capsule-mini.txt) — minimal seed
- [capsule-selfreconstructing.txt](./current/capsule-selfreconstructing.txt) — full self-reconstructing body
- [capsule-handshake.txt](./current/capsule-handshake.txt) — deterministic Mini → Full expansion
- [teof-shim.md](./current/teof-shim.md) — runtime rules for LLMs (determinism, Precedence, O–C–E–R–S)

## Integrity & provenance
- [hashes.json](./current/hashes.json) — SHA-256 digests (source of truth for bytes)
- [PROVENANCE.md](./current/PROVENANCE.md) — human freeze receipt
- [RELEASE.md](./current/RELEASE.md) — release notes / changes
- [reconstruction.json](./current/reconstruction.json) — machine recipe for reconstruction

## Tests / calibration
- [tests.md](./current/tests.md)
- [calibration.md](./current/calibration.md)

## Governance & scope
- See [`anchors/immutable.json`](../anchors/immutable.json) for immutable scope and policy.

---

**Runtime quick start:** Load `./current/capsule-mini.txt` + `./current/teof-shim.md` with temperature=0.  
**Maintenance note:** To publish a new version, create `capsule/vX.Y/…` and repoint the `capsule/current` symlink to the new folder. No README edits are required.
