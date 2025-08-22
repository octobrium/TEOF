# TEOF Seed (Bootstrap + Capsule)

This directory contains two things:

1) **Bootstrap** scripts to spin up a local run (venv → brief → anchor).
2) The **Capsule** (canonical texts + machine recipes) published under `./capsule/current/`.

---

## Quick Start (Bootstrap)

macOS/Linux:
~~~bash
bash seed/bootstrap.sh
~~~

Windows (PowerShell):
~~~powershell
.\seed\bootstrap.ps1
~~~

**What this does**
- Creates an isolated Python venv if missing.
- Runs the TEOF CLI to generate a brief:
  - writes to `artifacts/ocers_out/<timestamp>/`
  - updates/creates the `latest` symlink
- Appends a SHA-256 anchor for that run to `governance/anchors.json`.

> Runtime note: the capsule files are for documentation + reproducibility; the CLI run does **not** depend on them.

---

## Capsule (Canonical Entry Point)

**Stable entrypoint:** all canonical artifacts live under [`./capsule/current/`](./capsule/current/).  
`current` is a symlink to the latest version (`vX.Y/`). Update the symlink when you publish a new release.

### Contents (under `capsule/current/`)
- **Texts**
  - `capsule.txt` — full capsule  
  - `capsule-mini.txt` — minimal seed  
  - `capsule-selfreconstructing.txt` — self-reconstructing body  
  - `capsule-handshake.txt` — deterministic Mini → Full expansion  
  - `teof-shim.md` — runtime rules for LLMs (determinism, Precedence, O–C–E–R–S)
- **Integrity & provenance**
  - `hashes.json` — SHA-256 digests (source of truth for bytes)  
  - `PROVENANCE.md` — human freeze receipt  
  - `RELEASE.md` — release notes / changes  
  - `reconstruction.json` — machine recipe for reconstruction
- **Tests / calibration**
  - `tests.md`, `calibration.md`
- **Governance & scope**
  - See [`governance/anchors.json`](../../governance/anchors.json) for immutable anchors/scope.

---

## Publishing a New Capsule Version

1. Create a new version folder (copy from last release), e.g.:
   ~~~
   capsule/v0.1.1/
   ~~~
2. Update files as needed; recompute `hashes.json`; update `PROVENANCE.md` and `RELEASE.md`.
3. Point `current` to the new version:

   **macOS/Linux**
   ~~~bash
   cd capsule
   ln -sfn v0.1.1 current
   ~~~

   **Windows (PowerShell)**
   ~~~powershell
   cd seed\capsule
   if (Test-Path current) { rmdir current }
   cmd /c mklink /D current v0.1.1
   ~~~
   *(If symlinks are inconvenient, copy `v0.1.1` into `current`, but prefer a symlink.)*

4. Commit and tag the repo (e.g. `v0.1.1`).

---

## Expected Layout

~~~
seed/
├─ bootstrap.sh
├─ bootstrap.ps1
└─ capsule/
   ├─ v0.1.0/
   │  ├─ capsule.txt
   │  ├─ capsule-mini.txt
   │  ├─ capsule-selfreconstructing.txt
   │  ├─ capsule-handshake.txt
   │  ├─ teof-shim.md
   │  ├─ hashes.json
   │  ├─ PROVENANCE.md
   │  ├─ RELEASE.md
   │  └─ reconstruction.json
   └─ current -> v0.1.0
~~~

**Maintenance tip:** This README is *versionless*. Publishing a new capsule does not require editing this file—just update the `current` symlink.
