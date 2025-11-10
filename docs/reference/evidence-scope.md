# Evidence Scope

**Purpose:** enforce Principle P1.2 (Comprehensive Observation) by requiring every plan to cite both internal and external evidence, then capture a receipt proving the survey occurred before code changes leave the `queued` state.

## Structure

Plans that opt into schema `version >= 1` must include an `evidence_scope` object with four fields:

| Field | Required | Description |
| --- | --- | --- |
| `internal` | ✓ | References to TEOF-native artifacts (docs, memory, receipts, datasets) that motivate the work. Keep entries granular so future agents can replay the reasoning trail. |
| `external` | ✓ (or `comparative`) | References to literature, public telemetry, external datasets, or field measurements. URLs and DOI strings are fine; add a short `summary` so reviewers know why the citation matters. |
| `comparative` | optional (required when `external` empty) | Trends, benchmarks, or scaling studies that explain how the plan will move systemic axes. Use when contrasting multiple approaches or when no single external reference is decisive. |
| `receipts` | required before status `in_progress` | Paths (relative to repo root) to JSON receipts under `_report/…` that log the actual survey. The recommended location is `_report/agent/<id>/<plan_id>/evidence.json`. `_report/` receipts may remain untracked, but other paths (docs, datasets, etc.) must be in git. Include the plan id + step id when possible. |

Plans may be created with empty `receipts` while the survey dataset is being prepared, but you **must** attach at least one receipt before the plan status moves beyond `queued`. `tools/planner/validate.py` enforces this during strict validation, and the automation guards described below can block pushes when receipts are missing.

## Authoring workflow

1. Collect the evidence first—skim recent reflections, receipts, and external literature so you have real references before writing steps.
2. Run the planner scaffold with the new flags:

```bash
python -m tools.planner.cli new evidence-bridge \
  --summary "Bridge P1.2 evidence scope" \
  --plan-version 1 \
  --evidence-internal "docs/architecture.md::Repo layout contract" \
  --evidence-external "https://example.org/field-study::Field reliability benchmark" \
  --evidence-comparative "https://example.org/scaling-law::Agent vs human scaling curve" \
  --layer L4 --systemic-scale 6 --priority 1 --impact-score 80
```

3. Capture the survey receipt:

```bash
mkdir -p _report/agent/codex-5/2025-11-10-evidence-bridge
python scripts/tools/capture_evidence.py > \
  _report/agent/codex-5/2025-11-10-evidence-bridge/evidence.json
python -m tools.planner.cli attach-receipt \
  _plans/2025-11-10-evidence-bridge.plan.json S1 \
  --file _report/agent/codex-5/2025-11-10-evidence-bridge/evidence.json
```

4. Keep the scope in sync with plan edits. If you add a new external citation or discover a conflicting paper, update the `evidence_scope` block and capture a fresh receipt.

## Guard integration

- `teof operator verify --require-evidence-plan <plan_id>` now fails when the referenced plan is missing external references or receipts. Include this flag in your session bootstrap to prove comprehensive observation before touching the bus.
- `python -m tools.agent.push_ready --require-evidence-plan <plan_id>` blocks pushes until the plan’s evidence scope has both internal + external citations **and** at least one receipt (non-`_report/` paths must still be tracked).
- `python -m tools.planner.evidence_scope --all` emits an `_report/usage/evidence-scope/evidence-scope-<timestamp>.json` dashboard plus `latest.json`, summarizing how many v1 plans still lack citations or receipts. Add `--fail-on-missing` (and optionally `--fail-on-missing-receipts`) in CI to block merges when version ≥ 1 plans drift from P1.2.
- `tools/agent/preflight.sh full` now runs the evidence-scope CLI with both fail flags, so every preflight automatically records a coverage receipt and fails fast if any schema-v1 plan is missing citations or survey receipts.

Both guards rely on `tools/planner/evidence_scope.py`, which parses the plan, enforces category coverage, and checks receipt files (requiring git tracking only when the receipt lives outside `_report/`). Plans that stay on schema `version = 0` skip this enforcement, but the expectation is that new work (especially anything targeting S5+ axes) runs at `version = 1`.

## Receipts

Evidence receipts can be lightweight JSON payloads:

```json
{
  "schema": "teof.evidence.survey/v1",
  "plan_id": "2025-11-10-evidence-bridge",
  "collected_at": "2025-11-10T05:11:00Z",
  "internal": [
    {"ref": "docs/architecture.md", "summary": "Layer contracts require audit trails"}
  ],
  "external": [
    {"ref": "https://example.org/sre-transparency.pdf", "summary": "Field SRE transparency increases MTTR"}
  ],
  "comparative": [
    {"ref": "https://example.org/autogen-vs-teof", "summary": "Comparative agent governance run"}
  ],
  "notes": "Correlated P1.2 with REC-2025-05 external telemetry."
}
```

Store them under `_report/agent/<id>/<plan_id>/` so operator verify and receipt graph runs can ingest the provenance automatically.

## References

- [`docs/workflow.md`](../workflow.md) – Observation checklist now includes evidence verification.
- [`_plans/README.md`](../../_plans/README.md) – Schema details for `evidence_scope`.
- [`tools/planner/evidence_scope.py`](/tools/planner/evidence_scope.py) – Shared enforcement logic used by operator verify and push-ready.
