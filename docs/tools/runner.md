# Runner Tooling (Receipts & Cache)

`tools/runner/run.py` executes shell commands with deterministic receipts and optional caching. This keeps replicas auditable and avoids repeating expensive operations.

## Basic usage

```bash
python tools/runner/run.py -- ls -la
```

Outputs:

- `_report/runner/<timestamp>-<hash>.json` containing command, exit code, stdout/stderr, and metadata.
- `.cache/runner/<hash>.json` for cached replies (when `--cache` is used).

## Caching

```bash
python tools/runner/run.py --cache -- git status
```

Subsequent runs reuse the cached stdout/stderr unless `--force` is provided.

## Labels & receipts

```bash
python tools/runner/run.py --label "bootstrap" --cache -- ./tools/replica-smoke.sh
```

Include the receipt path in `memory/log.jsonl` for provenance.

## Safety notes

- The runner does **not** grant additional privileges. Commands still respect existing guardrails.
- Use `--force` to bypass cached results when side effects are required.
- Review receipts before sharing; redact sensitive data if necessary.

This tool is the first building block for orchestrating multi-step jobs. Pair it with the memory log to ensure every automated action leaves a verifiable trail.
