# ND-055 External Adoption Capsule Requirements (2025-11-09T05:44Z)

- Capsule contents: signed brief, CLI quickstart, telemetry hook instructions, authenticity receipts.
- Packaging format: tarball with metadata JSON (`capsule/<ver>/metadata.json`) referencing git commit + receipts.
- CLI `python -m tools.autonomy.adoption_capsule build --out ... --sign`.
- Telemetry handshake recorded in `_report/usage/external-adoption/summary-<ts>.json`.
