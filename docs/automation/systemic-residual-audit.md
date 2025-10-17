<!-- markdownlint-disable MD013 -->
# Systemic Residual Audit

**Status:** Checklist  
**Purpose:** Ensure no legacy OCERS artifacts remain after the systemic migration.

Run this audit monthly (or after large merges) to guarantee the codebase, docs, and
receipts stay aligned with the systemic lattice.

---

## 1. Automated checks

1. `rg -n "ocers" --glob '!_apoptosis/**'` – only historical docs within `_apoptosis/`
   or explicit migration notes should match.
2. `pytest tests/test_systemic_eval.py tests/test_systemic_rules.py` – confirms the
   systemic heuristic and rule helpers are intact.
3. `python3 tools/planner/validate.py --strict` – rejects plans missing systemic metadata.
4. `scripts/ci/quickstart_smoke.sh` – produces `artifacts/systemic_out/<stamp>/` receipts.
5. `scripts/ci/check_queue_template.py` – warns if queue templates reference OCERS fields.

Record command outputs under `_report/usage/` when running a formal audit.

---

## 2. Manual file inspection

| Target | Check | Notes |
|--------|-------|-------|
| `docs/automation.md` | Mentions `systemic` tooling throughout | No references to `ocers_out` |
| `_plans/**/*.plan.json` | Contains `systemic_targets`, `layer_targets`, `systemic_scale` | No `ocers_target` keys |
| `queue/*.md` | Declares `Systemic Targets:` / `Layer Targets:` headings | |
| `extensions/validator/` | Only `systemic_*` modules present | |
| `tools/planner/*.py` | Rely on `systemic_targets` helpers | |
| `docs/quickstart.md` | Guides users to systemic artifacts | |
| `docs/status.md` | Status sections reference systemic receipts | |

Flag anomalies in `_plans/next-development.todo.json` so the planner surface carries remediation tasks.

---

## 3. Capsule and governance artifacts

1. Review `capsule/v*/hashes.json` and confirm no `ocers` paths linger.
2. Scan `governance/anchors.json` for new `migration` or `dna-change` events;
   add one if systemic rules are materially updated.
3. Update `CHANGELOG.md` under “Docs/DNA” when systemic rules shift.

---

## 4. Receipts and dashboards

Ensure monitoring surfaces prefer systemic signals:

- `_report/usage/autonomy-footprint-baseline.json` – fields describe systemic automation.
- `_report/usage/onboarding/summary.json` – quickstart receipts reference `systemic_out`.
- Any analytics dashboards ingest the systemic lattice (axes + layers).

If legacy dashboards are still required for external reporting, document them explicitly
and scope them with migration deadlines.

---

## 5. Escalation

- If the audit uncovers non-trivial OCERS dependencies, open a plan (`S6`,`S4`, layer `L4`)
  to resolve them.
- When rules or tooling change, capture receipts in `_report/usage/` and update the
  inventory/progress docs.
- Escalate to governance (append-only anchors event) if systemic rules themselves change.

---

## 6. Audit log template

```
date: 2025-10-17
auditor: codex-4
commands:
  - rg -n "ocers" ...
  - pytest tests/test_systemic_eval.py tests/test_systemic_rules.py
  - python3 tools/planner/validate.py --strict
  - scripts/ci/quickstart_smoke.sh
findings: []
follow_up: []
```
