# OCERS Reference Inventory

Generated on 2025-10-16T23:04:28Z by codex-2

## Summary
- Total files containing `OCERS`: 184
- Inventory grouped by top-level directory for migration planning.
- Highest concentrations: `docs/` (48), `_plans/` (33), `queue/` (33), `_apoptosis/` (14) capturing both live surfaces and archived experiments.
- Queue metadata now relies on `Systemic Targets`/`Layer Targets`; legacy `OCERS Target` lines were removed during S3.

| Category | File count |
| --- | ---: |
| docs | 48 |
| _plans | 33 |
| queue | 33 |
| _apoptosis | 14 |
| extensions | 13 |
| _report | 7 |
| tools | 7 |
| governance | 5 |
| capsule | 4 |
| scripts | 4 |
| .github | 3 |
| [root] | 3 |
| tests | 3 |
| _bus | 2 |
| memory | 2 |
| teof | 2 |
| agents | 1 |

## docs (48)

- `docs/agents.md`
- `docs/alignment-protocol.md`
- `docs/architecture.md`
- `docs/automation.md`
- `docs/automation/autonomy-preflight.md`
- `docs/automation/backlog-health.md`
- `docs/automation/confidence-metrics.md`
- `docs/automation/ocers-overview.md`
- `docs/automation/ocers-systemic-mapping.md`
- `docs/ci-guarantees.md`
- `docs/decision-hierarchy.md`
- `docs/evangelism/demo-video-script.md`
- `docs/evangelism/one-pager.md`
- `docs/ideas/README.md`
- `docs/ideas/decentralized-teof-node.md`
- `docs/ideas/index.md`
- `docs/ideas/macro-hygiene-objectives.md`
- `docs/index.html`
- `docs/maintenance/repo-hygiene-20250922.md`
- `docs/observations/hyper-organism.md`
- `docs/policy/dev-accelerator.md`
- `docs/policy/fitness-lens.md`
- `docs/promotion-policy.md`
- `docs/proposals/20250827t192725z__item-01__draft.md`
- `docs/proposals/20250827t192725z__item-03__draft.md`
- `docs/proposals/20250827t192725z__item-04__draft.md`
- `docs/proposals/20250917t163219z__item-02__draft.md`
- `docs/proposals/20250917t163219z__item-03__draft.md`
- `docs/proposals/20250917t163219z__item-04__draft.md`
- `docs/proposals/20250920t211606z__proposal-sync.md`
- `docs/proposals/20250920t215400z__receipts-observability__draft.md`
- `docs/proposals/20250922t190055z__decentralized-propagation-pilot__draft.md`
- `docs/proposals/readme.md`
- `docs/quick-links.json`
- `docs/quick-links.md`
- `docs/quickstart.md`
- `docs/specs/backfill.md`
- `docs/specs/connectivity.md`
- `docs/specs/recursive-integrity.md`
- `docs/teps/tep-0000-template.md`
- `docs/usage/autonomous-node/20251012T193658Z/scan/ethics.json`
- `docs/usage/autonomous-node/20251012T193658Z/scan/scan.json`
- `docs/usage/direction-metrics.md`
- `docs/vision/relay-offering-collateral.md`
- `docs/vision/relay-offering-sample-brief.md`
- `docs/vision/teof-future.md`
- `docs/whitepaper.md`
- `docs/workflow.md`

## _plans (33)

- `_plans/2025-09-17-convergence-metrics.plan.json`
- `_plans/2025-09-17-queue-hygiene.plan.json`
- `_plans/2025-09-18-backlog-refresh.plan.json`
- `_plans/2025-09-18-codex4-consensus-draft.plan.json`
- `_plans/2025-09-19-kernel-slimdown.plan.json`
- `_plans/2025-09-21-code-compaction.justification.md`
- `_plans/2025-09-21-code-compaction.plan.json`
- `_plans/2025-09-21-consensus-ci-integration.plan.json`
- `_plans/2025-10-03-2025-10-04-plan-metadata-backfill-phase2.plan.json`
- `_plans/2025-10-03-authenticity-metadata-backfill.justification.md`
- `_plans/2025-10-03-authenticity-metadata-backfill.plan.json`
- `_plans/2025-10-03-autonomy-metadata-backfill.justification.md`
- `_plans/2025-10-03-autonomy-metadata-backfill.plan.json`
- `_plans/2025-10-03-autonomy-roadmap-metadata.justification.md`
- `_plans/2025-10-03-autonomy-roadmap-metadata.plan.json`
- `_plans/2025-10-03-capsule-metadata-backfill.justification.md`
- `_plans/2025-10-03-capsule-metadata-backfill.plan.json`
- `_plans/2025-10-03-external-metadata-backfill.justification.md`
- `_plans/2025-10-03-external-metadata-backfill.plan.json`
- `_plans/2025-10-03-governance-metadata-backfill.justification.md`
- `_plans/2025-10-03-governance-metadata-backfill.plan.json`
- `_plans/2025-10-03-heartbeat-metadata-backfill.justification.md`
- `_plans/2025-10-03-heartbeat-metadata-backfill.plan.json`
- `_plans/2025-10-03-plan-metadata-backfill.plan.json`
- `_plans/2025-10-03-planner-metadata-backfill.justification.md`
- `_plans/2025-10-03-planner-metadata-backfill.plan.json`
- `_plans/2025-10-03-reconcile-metadata-backfill.justification.md`
- `_plans/2025-10-03-reconcile-metadata-backfill.plan.json`
- `_plans/2025-10-04-planner-metadata-backfill-phase3.plan.json`
- `_plans/2025-10-04-slow-plan-latency.plan.json`
- `_plans/2025-10-05-ocers-scan-automation.plan.json`
- `_plans/2025-10-06-ocers-systemic-alignment.plan.json`
- `_plans/next-development.todo.json`

## queue (33)

- `queue/000-welcome.md`
- `queue/001-agent-bus-watch.md`
- `queue/002-bus-status-filters.md`
- `queue/005-bus-message-cli.md`
- `queue/006-task-assign-bus-message.md`
- `queue/007-bus-event-severity.md`
- `queue/008-bus-status-staleness.md`
- `queue/009-bus-watch-window.md`
- `queue/010-collab-support.md`
- `queue/011-bus-tooling-review.md`
- `queue/012-bus-message-claim-guard.md`
- `queue/013-maintenance-pruning.md`
- `queue/014-claim-seed-docs.md`
- `queue/015-prune-script.md`
- `queue/030-consensus-ledger-cli.md`
- `queue/031-consensus-receipts.md`
- `queue/032-consensus-cadence.md`
- `queue/033-consensus-dashboard.md`
- `queue/034-governance-l4-binding.md`
- `queue/034-l4-binding-brief.md`
- `queue/035-capsule-status-ledger.md`
- `queue/036-macro-hygiene-objective.md`
- `queue/037-manifest-swap-helper.md`
- `queue/038-ci-consensus-integration.md`
- `queue/039-capsule-cadence-plan.md`
- `queue/040-code-compaction.md`
- `queue/041-session-sync.md`
- `queue/042-coordination-dashboard.md`
- `queue/044-dirty-handoff-automation.md`
- `queue/045-session-guard-upgrade.md`
- `queue/046-dirty-handoff-autoresolver.md`
- `queue/047-relay-case-study-publish.md`
- `queue/048-repo-anatomy-dashboard.md`

## _apoptosis (14)

- `_apoptosis/20250828T190533Z/experimental/experiments/extensions/cli/generators/hybrid_gen.py`
- `_apoptosis/20250828T190533Z/experimental/experiments/extensions/cli/validate.py`
- `_apoptosis/20250828T190533Z/experimental/ops/aggregate_reference_results.py`
- `_apoptosis/20250828T190533Z/experimental/ops/url_to_ocers.command`
- `_apoptosis/20250828T190533Z/experimental/ops/url_to_ocers.sh`
- `_apoptosis/20250828T190533Z/experimental/packages/ocers/README.md`
- `_apoptosis/20250828T190533Z/experimental/packages/ocers/ocers/cli.py`
- `_apoptosis/20250828T190533Z/experimental/packages/ocers/pyproject.toml`
- `_apoptosis/20250828T190533Z/teof/bootloader.py`
- `_apoptosis/20250828T190533Z/teof/eval/ocers_min.py`
- `_apoptosis/20250828T190533Z/teof/teof_eval.py`
- `_apoptosis/20250917T181243Z/001-anchors-guard.md`
- `_apoptosis/20250917T181243Z/002-kelly-ledger.md`
- `_apoptosis/20250917T181243Z/003-ocers-upgrade.md`

## extensions (13)

- `extensions/cli/generators/hybrid_gen.py`
- `extensions/cli/validate.py`
- `extensions/prompts/philosophy.py`
- `extensions/scoring/README.md`
- `extensions/scoring/teof_score.py`
- `extensions/validator/README.md`
- `extensions/validator/RUNTIME_SWAP.md`
- `extensions/validator/ocers.schema.json`
- `extensions/validator/ocers_rules.py`
- `extensions/validator/prompt_ocers.txt`
- `extensions/validator/scorers/ensemble.py`
- `extensions/validator/teof_ocers_min.py`
- `extensions/validator/teof_validator.py`

## _report (7)

- `_report/agent/codex-1/backlog-refresh/analysis-20250918T192600Z.md`
- `_report/agent/codex-1/idle-pickup/analysis-20250918T203200Z.md`
- `_report/agent/codex-2/consensus-ci/notes.md`
- `_report/agent/codex-2/kernel-slimdown/deterministic-coverage.md`
- `_report/agent/codex-2/kernel-slimdown/heuristic-audit.md`
- `_report/agent/codex-4/consensus/context-20250918T1928Z.md`
- `_report/usage/prompts/philosophy-20251004T165612Z.md`

## tools (7)

- `tools/autocollab.sh`
- `tools/autonomy/scan_driver.py`
- `tools/backfill/emit_queue.py`
- `tools/fractal/__init__.py`
- `tools/fractal/backfill_plans.py`
- `tools/fractal/conformance.py`
- `tools/planner/cli.py`

## governance (5)

- `governance/CHARTER.md`
- `governance/core/L5 - workflow/fitness-lens copy.md`
- `governance/core/L5 - workflow/workflow.md`
- `governance/core/emergent-principles.jsonl`
- `governance/policy.json`

## capsule (4)

- `capsule/v1.5/OGS-spec.md`
- `capsule/v1.5/volatile-data-protocol.md`
- `capsule/v1.6/OGS-spec.md`
- `capsule/v1.6/volatile-data-protocol.md`

## scripts (4)

- `scripts/bot/autocollab.py`
- `scripts/bot/doc_autopr.py`
- `scripts/ci/check_queue_template.py`
- `scripts/ops/build_system_prompt.py`

## .github (3)

- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/teof-ci.yml`
- `.github/workflows/teof-doc-autopr.yml`

## [root] (3)

- `.gitignore`
- `README.md`
- `pyproject.toml`

## tests (3)

- `tests/test_backlog_health.py`
- `tests/test_ocers_eval.py`
- `tests/test_planner_cli.py`

## _bus (2)

- `_bus/messages/APOP-007.jsonl`
- `_bus/messages/manager-report.jsonl`

## memory (2)

- `memory/log.jsonl`
- `memory/reflections/reflection-20250926T202850Z.json`

## teof (2)

- `teof/eval/__init__.py`
- `teof/eval/ocers_min.py`

## agents (1)

- `agents/tasks/tasks.json`
