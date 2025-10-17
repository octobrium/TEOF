# Task: Build manifest/branch swap helper
Goal: ship a helper (script or CLI) that backs up and restores `AGENT_MANIFEST.json` + agent branches so sessions stay clean.
Notes: align with docs/maintenance/macro-hygiene.md (environment hygiene bullet); include example usage and receipts in docs/agents.md.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S4 Defense, S5 Intelligence, S6 Truth, S10 Meaning
Layer Targets: L5 Workflow
Sunset: retire once the helper becomes part of the capsule toolchain.
Fallback: keep manually stashing manifests before each session.
