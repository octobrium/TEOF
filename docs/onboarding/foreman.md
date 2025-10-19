# Conversational Foreman

The `teof foreman` command lets you stay in plain language while it dispatches
to the correct TEOF workflow. Instead of remembering which CLI takes which
flags, ask for what you want and the foreman runs the underlying command with
sane defaults.

## Quick start

```bash
python -m teof.cli foreman --say "run the alignment scan"
python -m teof.cli foreman --say "show me the status"
python -m teof.cli foreman --say "list today's tasks"
python -m teof.cli foreman --say "rebuild the brief"
```

Call `python -m teof.cli foreman` with no arguments to be prompted interactively.

## What it covers today

| Request style | Routed command | Behaviour |
| --- | --- | --- |
| “run the alignment scan”, “check alignment” | `teof scan --summary` | Executes the scan driver with summary output (limit 10). |
| “show the status”, “what’s the state” | `teof status` | Prints the repo status snapshot. |
| “list tasks”, “what’s next” | `teof tasks` | Shows the active task table with warnings. |
| “rebuild the brief” | `teof brief` | Regenerates the bundled brief ensemble. |
| “daily cycle”, “run my routine” | `status → scan → tasks` | Runs the daily alignment cadence (status, scan summary, task snapshot). |
| “help” | _Foreman help_ | Displays supported phrases and tips. |

The matcher is keyword-based, so keep the intent words (scan, status, tasks,
brief) in your sentence. If the foreman cannot map a request, it prints examples
you can try.

## Extending the foreman

- Update `teof/commands/foreman.py` to add new keyword → action mappings.
- Keep actions reversible and receipt-backed. When you add a new action, link
  the resulting receipts in `_plans/` or `_report/` as usual.
- For multi-step flows (e.g., plan scaffolding + scan), consider wrapping them
  in helper functions so the foreman only has to call one callable.

This conversational layer is intentionally minimal—it is a thin bridge between
plain requests and the audited automation the rest of TEOF enforces.
