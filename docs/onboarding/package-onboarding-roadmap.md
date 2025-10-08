# Package & Onboarding Roadmap (2025-09-26)

## Objectives
- Make `pip install teof` (or equivalent wheel) the canonical entry point for
  new users.
- Deliver a 10-minute quickstart that installs dependencies, runs `teof brief`,
  and surfaces receipts under `_report/usage/onboarding/`.
- Automate a guard that reruns the quickstart in CI so it stays aligned.

## Current State
- `pyproject.toml` publishes the `teof` package (editable install assumed).
- Quickstart instructions (`docs/quickstart.md`) describe manual steps; no
  automated verification exists.
- Packaging assets (README classifiers, versioning, wheel metadata) are minimal.

## Proposed Work

### S1 — Package core CLI for distribution
- Produce a source/wheel build via `python -m build` and ensure console scripts
  (`teof`, `teof-validate`, etc.) work when installed in a clean venv.
- Update metadata: classifiers, description, long_description render check.
- Capture receipts: `_report/usage/onboarding/build-<timestamp>.json` summarises
  build + install test.

### S2 — Ten-minute onboarding guide
- Script the quickstart (`scripts/onboarding/install_quickstart.sh` or
  `python -m tools.onboarding.quickstart`) that:
  1. Creates/activates a venv.
  2. Installs the package from local wheel or index.
  3. Runs `teof brief` and validates artifacts.
  4. Prints next steps (bus, plans).
- Document in `docs/onboarding/quickstart.md` with copy/paste commands and
  expected receipts.

### S3 — Automated verification
- Add a CI target (GitHub Action + `make quickstart-check`) that executes the
  onboarding script on every PR touching packaging/docs.
- Emit receipts to `_report/usage/onboarding/ci/<timestamp>.json` for audit.
- Wire failures into `tools.autonomy.objectives_status` (new field under O3/O5).

## Deliverables & Receipts
| Artifact | Path |
| --- | --- |
| Build receipt | `_report/usage/onboarding/build-*.json` |
| Quickstart script | `scripts/onboarding/install_quickstart.sh` (or equivalent) |
| Quickstart doc | `docs/onboarding/quickstart.md` |
| CI config | `.github/workflows/onboarding.yml` (or augmented existing workflow) |

## Open Questions
- Should we publish to TestPyPI first or keep installs local-only until ready?
- How do we version receipts for multiple Python versions (3.9–3.12)?
- Do we bundle sample data (docs/examples) with the wheel or fetch on demand?

## Next Actions
1. Prototype the build/install flow in a clean venv and capture a build receipt.
2. Draft the onboarding script + doc, ensuring timestamps and symlinks remain deterministic.
3. Add CI plumbing and update objectives status once the onboarding guard exists.
