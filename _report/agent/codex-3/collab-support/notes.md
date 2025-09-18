# Collab Support — Survey Notes (S1)

## Existing Guidance
- `docs/AGENTS.md` covers core coordination tools but lacks explicit instructions for idle agents.
- `docs/parallel-codex.md` encourages keeping `bus_watch` running and using `bus_message`, yet offers no cadence for availability pings.

## Bus Activity Patterns
- Recent coordination relied on ad-hoc updates (e.g., agents posting “available for support” via `bus_message`).
- Manager backlog entry `QUEUE-010` requests formalizing this behaviour.

## Gaps Identified
- No standard timing for idle announcements or escalation after extended idle time.
- No reusable command templates/aliases to minimise friction when offering help.

Next: draft the workflow (S2) and publish documentation/receipts (S3).
