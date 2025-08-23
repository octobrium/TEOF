# Promotion Policy (experimental → extensions)

Goal: keep the kernel tiny, deterministic, auditable. Promote only proven modules.

Folders
- extensions/ — canonical, packaged, used by CLI/CI; subject to provenance & changelog
- experimental/ — active candidates; not packaged
- archive/ — frozen history; not maintained; not in CI

Promotion criteria (all required)
1. Determinism: same inputs → identical outputs across 3 clean runs (document how)
2. Spec alignment: matches current OCERS/OGS shapes; rule changes include updated goldens + short TEP
3. CI coverage: enforced via docs/examples/**; regressions fail CI
4. Minimal surface: no hidden state; clear main(); minimal deps; import path extensions.…
5. Provenance: append-only event in governance/anchors.json referencing prev_content_hash for promoted logic
6. Docs: Quickstart or module README updated so newcomers can reproduce artifacts exactly

De-promotion / freezing
- Non-compliant modules move to archive/ with “frozen as of <date/tag>”.

Packaging rule
- Only extensions/ is packaged/exposed via console scripts. CI fails if it imports experimental/ or archive/.

Release hygiene
- Every release runs scripts/freeze.sh to refresh hashes, write an anchors event, update CHANGELOG, and tag.
