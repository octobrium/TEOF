# Task: Build manifest/branch swap helper
Goal: ship a helper (script or CLI) that backs up and restores `AGENT_MANIFEST.json` + agent branches so sessions stay clean.
Notes: align with docs/maintenance/macro-hygiene.md (environment hygiene bullet); include example usage and receipts in docs/agents.md.
OCERS Target: Reproducibility↑ Self-repair↑
Coordinate: S3:L5
Sunset: retire once the helper becomes part of the capsule toolchain.
Fallback: keep manually stashing manifests before each session.
