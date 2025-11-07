# Quickstart

Before running the smoke test, verify your environment with `bin/teof-syscheck`
or use the orchestrated `bin/teof-up` entrypoint. Repeat runs can reuse the
cached onboarding environment with `bin/teof-up --fast` (only after you have
completed a full run at least once).

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

> Example quickstart receipt structure (truncated):
```jsonc
{
  "install_source": "wheel",
  "wheel": "dist/teof-0.1.0a2-py3-none-any.whl",
  "teof_brief": {
    "returncode": 0,
    "stdout": "brief: wrote artifacts/systemic_out/20251003T191825Z\n",
    "stderr": ""
  },
  "artifacts": {
    "latest_symlink": "artifacts/systemic_out/latest",
    "latest_target": "artifacts/systemic_out/20251003T191825Z"
  },
  "run": {
    "reuse_venv": false,
    "skip_install": false
  },
  "generated_at": "2025-10-03T19:18:25Z",
  "python": "3.9.6 (default, Apr 30 2025, 02:07:17) [Clang 17.0.0 (clang-1700.0.13.5)]",
  "venv": ".cache/onboarding-venv"
}
```

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
- Join the coordination bus so other agents know you're online: `python -m tools.agent.session_boot --agent <id> --focus <role> --with-status`, then claim work with `python -m tools.agent.bus_claim claim --task <task_id> --plan <plan_id>` and stream updates via `python -m tools.agent.bus_event log --event status ...`. The full flow is captured in `docs/onboarding/README.md` (steps 5–7) and [`docs/parallel-codex.md`](parallel-codex.md).
- Backlog every vetted idea immediately with `python -m tools.planner.cli new ... --priority <0..n> --layer <L?> --systemic-scale <1..10> --impact-score <n>`. The systemic ladder lives in [`docs/foundation/systemic-scale.md`](docs/foundation/systemic-scale.md).
- If you change validator behaviour, update the goldens under `docs/examples/**/expected/`
- When packaging for others, freeze the capsule (`scripts/freeze.sh`) and append a governance anchor
- Inspect the memory layer to resume prior runs: `teof memory doctor`, `teof memory timeline`, or `teof memory diff --run <id>`. Promote any durable facts via `tools/memory/memory.py` helpers so future sessions inherit your context.
