# Repo Hygiene Inventory — 2025-09-22

Command snapshot (`du -sh * | sort -h`):

```
AGENT_MANIFEST.codex-4.json        4.0K
AGENT_MANIFEST.codex-manager.json  4.0K
AGENT_MANIFEST.example.json        4.0K
AGENT_MANIFEST.json                4.0K
CHANGELOG.md                       4.0K
CODE_OF_CONDUCT.md                 4.0K
CONTRIBUTING.md                    4.0K
LICENSE                            4.0K
NOTICE                             4.0K
pyproject.toml                     4.0K
SECURITY.md                        4.0K
README.md                          8.0K
agents                             20K
memory                             20K
teof.egg-info                      24K
teof                               36K
bin                                52K
datasets                           72K
extensions                         96K
queue                              108K
capsule                            148K
governance                         148K
scripts                            192K
tests                              420K
docs                               496K
_plans                             656K
tools                              752K
_bus                               780K
_apoptosis                         1.8M
artifacts                          5.9M
_report                            6.7M
```

Preliminary cleanup candidates:

- **`AGENT_MANIFEST.*` duplicates** – keep `AGENT_MANIFEST.json` as active manifest, move variants into `docs/examples/agents/` (or merge into a single commented template) to reduce top-level clutter.
- **`_apoptosis/` (1.8 MB)** – contains legacy apoptosis run logs; confirm with automation owners whether these can relocate to `artifacts/` or be pruned after archiving latest summary.
- **`artifacts/` (5.9 MB)** – retains historical OCERS outputs; evaluate keeping only `latest/` and relocating dated snapshots to release tags.
- **`_report/` (6.7 MB)** – largest footprint; propose rotation policy (retain last N runs) for directories like `_report/usage/external-summary.json` and `_report/usage/chronicle/` now that canonical ledgers exist.
- **`queue/` + `agents/tasks/tasks.json`** – confirm if legacy queue fixtures are still referenced; otherwise consolidate into `_plans/` or documentation.
- **`binary scripts` under `bin/`** – audit for redundancy with Python entrypoints (`teof bootloader`, `tools/…`).

Next steps:
1. Validate which artifacts are required for audits vs safe to archive.
2. Draft retention policy + automation scripts for `_report/` and `artifacts/`.
3. Prepare PR removing/moving duplicates once stakeholders confirm.

## Update — 2025-09-23

- `tools.autonomy.actions.hygiene` now orchestrates receipt rotation and delegates
  stale-plan pruning to `tools.maintenance.prune_artifacts`, producing a single
  receipt under `_report/usage/autonomy-actions/` that records both actions.
- When the autonomy loop runs with apply privileges, stale plans and reports
  older than the cutoff automatically migrate into `_apoptosis/<stamp>/`,
  keeping the evergreen backlog lean without duplicative tooling.
- The hygiene action now defaults to pruning only `_report/*` targets; pass an
  explicit `prune_targets` list if you intend to sweep other paths (e.g., legacy
  plans) so CI fixtures stay intact. Dry-run receipts always preserve the full
  candidate list for optional follow-up.

## Update — 2025-10-04

- Root-level manifest variants (`AGENT_MANIFEST.codex-2/3/4.json`) now live under
  `docs/examples/agents/`; only the active `AGENT_MANIFEST.json` remains at the
  repo root so manifests stay tidy between seat swaps.
