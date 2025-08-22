# TEOF Capsule (Directory README)

This folder holds the versioned capsule and a symlink named `current` that points to the latest immutable release.

- `vX.Y/` — immutable capsule release (human + machine artifacts)
- `current -> vX.Y` — symlink to the active release

## Canonical artifacts (inside `./current/`)
- capsule.txt — full capsule
- capsule-mini.txt — minimal seed
- capsule-selfreconstructing.txt — self-reconstructing body
- capsule-handshake.txt — deterministic Mini → Full expansion
- teof-shim.md — runtime rules for LLMs (determinism, Precedence, O–C–E–R–S)
- hashes.json — SHA-256 digests (source of truth for bytes)
- PROVENANCE.md — human freeze receipt
- RELEASE.md — release notes / changes
- reconstruction.json — machine recipe for reconstruction
- tests.md, calibration.md

Governance & scope: see `../../governance/anchors.json`.

## Switch `current` to a new release

macOS / Linux (Terminal):

    cd seed/capsule
    ln -sfn v0.1.1 current

Windows (PowerShell):

    cd seed\capsule
    if (Test-Path current) { rmdir current }
    cmd /c mklink /D current v0.1.1

This README is intentionally short to avoid duplication. Full bootstrap & capsule docs live in `seed/README.md`.
