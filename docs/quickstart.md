# Quickstart

<!-- generated: quickstart snippet -->
Run this smoke test on a fresh checkout:
```bash
python3 -m pip install -e .
teof brief
ls artifacts/systemic_out/latest
cat artifacts/systemic_out/latest/brief.json
```

- Install exposes the teof console script.
- teof brief scores docs/examples/brief/inputs/ and writes receipts under artifacts/systemic_out/<UTC>.

> Update the snippet via `python3 tools/snippets/render_quickstart.py` after editing `tools/snippets/quickstart.json`.

## Extend the run (optional)
To score your own systemic readiness drafts, point the ensemble CLI at any directory of `.txt` files:
```bash
python3 -m extensions.validator.scorers.ensemble_cli \
  --in /path/to/notes \
  --out artifacts/systemic_out/$(date -u +%Y%m%dT%H%M%SZ)
```

For the minimal validator only, use:
```bash
python3 -m extensions.validator.teof_systemic_min input.txt artifacts/outdir
```

## Next checkpoints
- Join the coordination bus so other agents know you're online: `python -m tools.agent.session_boot --agent <id> --focus <role> --with-status`, then claim work with `python -m tools.agent.bus_claim claim --task <task_id> --plan <plan_id>` and stream updates via `python -m tools.agent.bus_event log --event status ...`. See [`docs/parallel-codex.md`](parallel-codex.md) for the full session loop.
- Backlog every vetted idea immediately with `python -m tools.planner.cli new ... --priority <0..n> --layer <L?> --systemic-scale <1..10> --impact-score <n>`. The systemic ladder lives in [`docs/foundation/systemic-scale.md`](docs/foundation/systemic-scale.md).
- If you change validator behaviour, update the goldens under `docs/examples/**/expected/`
- When packaging for others, freeze the capsule (`scripts/freeze.sh`) and append a governance anchor
- Inspect the memory layer to resume prior runs: `teof memory doctor`, `teof memory timeline`, or `teof memory diff --run <id>`. Promote any durable facts via `tools/memory/memory.py` helpers so future sessions inherit your context.
