# Idle-Agent Collaboration Workflow (Draft)

## Announce Availability
- Within 5 minutes of releasing a claim, log:
  ```bash
  python -m tools.agent.bus_event log --event status \
    --summary "<agent-id> idle; available for support" \
    --task QUEUE-010 --plan 2025-09-18-collab-support
  ```
- Mirror via `bus_message --task QUEUE-010 --type status --summary "<agent-id> available"` (include focus tags if useful).

## Monitor & Offer Help
- Keep `python -m tools.agent.bus_watch --limit 20 --follow --window-hours 4` running.
- When blockers appear, respond using `bus_message --type status` (add `--meta reviewer=<id>` for reviews).
- If unassigned tasks persist, ping the manager referencing `_bus/claims/<task>.json`.

## Escalate When Needed
- After 30 minutes idle, send `bus_message --meta escalation=needed` on `QUEUE-010` to request direction.
- Once reassigned, claim the task, log a status event, and stop advertising availability.

## Shell Aliases
```bash
alias bus_idle="python -m tools.agent.bus_event log --event status --summary 'codex-3 idle; available for support' --task QUEUE-010 --plan 2025-09-18-collab-support"
alias bus_offer="python -m tools.agent.bus_message --task QUEUE-010 --type status --summary 'codex-3 can assist on <task>' --meta agent=codex-3"
```
