# TEOF Quickstart (10-minute path)

> Looking for the full onboarding map? Start with
> `docs/onboarding/README.md` and return here when you need the
> step-by-step quickstart receipts.

## One-command bootstrap

Run `bin/teof-up` from the repository root to:

- build the distributable artifacts (`python3 -m tools.onboarding.build`),
- execute the guarded quickstart flow (`python3 -m tools.onboarding.quickstart`), and
- rerun the quickstart smoke check (`scripts/ci/quickstart_smoke.sh`).

The script captures receipts under `_report/usage/onboarding/` and prints links to the next docs to read.
After the first successful run you can refresh receipts quickly with
`bin/teof-up --fast`, which reuses the cached onboarding virtualenv instead of
rebuilding it.

## Manual workflow (two commands)

Run these commands from the repository root to install TEOF in a fresh virtual
environment, execute `teof brief`, and capture receipts.

```bash
python3 -m tools.onboarding.build
python3 -m tools.onboarding.quickstart
```

What happens:
1. `tools.onboarding.build` installs the `build` module if needed, builds the
   wheel/sdist into `dist/`, and writes a receipt under
   `_report/usage/onboarding/build-<UTC>.json` with hashes and metadata.
2. `tools.onboarding.quickstart` creates `.cache/onboarding-venv`, installs the
   latest wheel (fallback: editable install), runs `teof brief`, and emits a
   receipt under `_report/usage/onboarding/quickstart-<UTC>.json`.

After the run you'll find:
- A clean virtualenv at `.cache/onboarding-venv/`.
- `artifacts/systemic_out/<timestamp>/` populated by `teof brief` (symlinked by
  `artifacts/systemic_out/latest`).
- Receipts summarising the build and quickstart under `_report/usage/onboarding/`.

> Tip: rerun `python3 -m tools.onboarding.quickstart --editable` if you want to
> test the editable install instead of wheel-based distribution.

## CI guard
Once the onboarding workflow is wired into CI, failures in the quickstart step
will surface as build failures and the objectives status (O3/O5) will flag the
issue automatically.
