## Systemic Scoring Ensemble

Legacy loop-specific scorers have been retired. The scoring surface is now the
systemic readiness ensemble exposed through `extensions.validator.scorers.ensemble`.

### Quick reference

- `extensions/validator/teof_systemic_min.py` — CLI wrapper that scores a single
  text file against the systemic heuristic.
- `extensions/validator/scorers/ensemble.py` — loads the heuristic runner(s) and
  produces aggregated scores used by `teof brief`.

```bash
# Run the heuristic directly
python3 -m extensions.validator.teof_systemic_min docs/examples/brief/inputs/001_whitehouse_ai.txt artifacts/systemic_out/tmp

# Run the ensemble scorer used by teof brief
python3 -m extensions.validator.scorers.ensemble docs/examples/brief/inputs/001_whitehouse_ai.txt
```

See `docs/automation/systemic-overview.md` for the migration notes and how the
systemic axes replace earlier observation loops. The ensemble module accepts
additional runners via `register_runner()` if downstream tooling wants to add
more signals.
