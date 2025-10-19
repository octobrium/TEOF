# Exploratory Plans

This lane holds provisional plans created with `teof-plan new <slug> --exploratory`.

- Plans here may omit some metadata that the canonical `_plans/` entries require.
- Every exploratory plan includes an auto-expiry horizon; promote or retire the plan before that timestamp.
- Receipts produced during exploratory work should live under `_report/exploratory/<plan_id>/`.
- Before promoting changes into the constitutional lanes, convert the plan into a canonical entry (`teof-plan new …` without `--exploratory`) and migrate the receipts.
- `_report/exploratory/` is ignored by default; when a receipt graduates into the canonical flow, add it back with `git add -f _report/exploratory/<plan_id>/…` or relocate it under the standard `_report/` paths.
