# Session Guard

TEOF now blocks bus-facing commands unless the caller has a fresh
`session_boot` receipt. The guard keeps parallel agents from colliding by
ensuring every seat announces itself, tails the manager-report lane, and
captures the evidence before mutating claims or messages.

## What is enforced
- `python -m teof bus_claim` (claim/release)
- `python3 -m teof bus_event`
- `python -m tools.agent.bus_message`
- `python -m tools.agent.bus_ping`
- Helpers that call the above (`directive_pointer`, `task_assign`, etc.)

Each command resolves the agent id from `AGENT_MANIFEST.json`, verifies it
matches the explicit `--agent` value (if any), and checks for
`_report/session/<agent>/manager-report-tail.txt` with a `captured_at` header
not older than the freshness threshold (default: 3,600 s).

## How to stay green
1. Run `python -m tools.agent.session_boot --agent <id> --focus <role> --with-status`
   at the start of the session.
2. Keep the manifest in sync (`python -m tools.agent.manifest_helper activate <id>`)
   before swapping seats.
3. Repeat `session_boot` if you have been idle for more than an hour or after
   checking out a new branch.

If the guard fails you will see an error similar to:
```
session guard: no manager-report tail for codex-4. Run `python -m tools.agent.session_boot --agent codex-4 --with-status` before using bus commands.
```

The guard also records the failure under
`_report/agent/<id>/session_guard/events.jsonl` so other operators can audit the
override trail.

## Overrides (use sparingly)
- `--allow-stale-session` lets the command proceed while still logging a
  `session_override` event.
- `--session-max-age <seconds>` adjusts the freshness window for one call.
- `TEOF_SESSION_MAX_AGE=<seconds>` sets a process-wide default.
- `TEOF_SESSION_GUARD_DISABLED=1` (tests only) bypasses the guard entirely.

Overriding the guard without an accompanying receipt should be treated as a
policy violation—refresh the handshake instead.

## Receipts emitted
| Trigger | Receipt | Purpose |
| --- | --- | --- |
| Missing manager tail | `_report/agent/<id>/session_guard/events.jsonl` | Logs `session_missing` with context |
| Corrupt receipt | `_report/.../session_guard/events.jsonl` | Logs `session_invalid` |
| Stale handshake | `_report/.../session_guard/events.jsonl` | Logs `session_stale`+`session_override` (if bypassed) |

Use these receipts in plans when proving an operator refreshed the guard and
returned to compliance.
