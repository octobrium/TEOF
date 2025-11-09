# Idle-Agent Collaboration Workflow

This workflow helps agents broadcast availability, offer assistance, and avoid coordination gaps when they have free cycles.

## 1. Announce Availability
- Within 5 minutes of going idle, run:
  ```bash
  python3 -m teof bus_event log --event status \
    --summary "<agent-id> idle; available for support" \
    --task QUEUE-010 --plan 2025-09-18-collab-support
  ```
- Mirror the update with a bus message (optionally include focus areas):
  ```bash
  python -m teof bus_message --task QUEUE-010 --type status \
    --summary "<agent-id> available for support (focus: docs/tests)" \
    --meta agent=<agent-id>
  ```

## 2. Monitor & Offer Help
- Keep `python3 -m teof bus_watch --limit 20 --follow --window-hours 4` open (legacy path: `python -m tools.agent.bus_watch`; default window=24h—pass `--window-hours 0` for the full log) and schedule `python -m tools.agent.bus_heartbeat --dry-run` so stale manager heartbeats or idle claims raise receipts automatically.
- When another agent posts blockers or a manager flags open work, reply with a `bus_message --type status` offering help. Add `--meta reviewer=<agent-id>` if reviewing.
- If a task lacks an assignee, ping the manager with a `bus_message` referencing `_bus/claims/<task>.json`.

## 3. Escalation & Hand-off
- If you remain idle for more than 30 minutes, escalate with:
  ```bash
  python -m teof bus_message --task QUEUE-010 --type status \
    --summary "<agent-id> still idle; request guidance" \
    --meta escalation=needed
  ```
- Once assigned, immediately claim the task via `bus_claim`, log a status event, and stop broadcasting availability.

## 4. Optional Shell Aliases
```bash
alias bus_idle="python3 -m teof bus_event log --event status --summary 'codex-3 idle; available for support' --task QUEUE-010 --plan 2025-09-18-collab-support"
alias bus_offer="python -m teof bus_message --task QUEUE-010 --type status --summary 'codex-3 can assist on <task>' --meta agent=codex-3"
```
Adjust the aliases for your agent id or preferred templates.

## 5. Log Follow-ups
- After you action a coordination request (rerunning CI, syncing tasks, etc.), capture the command output under `_report/agent/<id>/support/` and log it via `python3 -m teof bus_event log --event status --summary "<agent-id> completed <follow-up>" --receipt <path>`.
- Mirror the status on the relevant bus message thread (`manager-report` or the task file) with `python -m teof bus_message --task <id> --type status --summary "<agent-id> completed follow-up" --receipt <path>` so managers can trace the breadcrumb.
- Reference the follow-up entries in your next handoff or plan notes to close the loop.

## 6. Review & Sunset
- Revisit this cadence after two sprints; if automation replaces manual updates, sunset the workflow.
- Keep receipts (bus events/messages) so managers can audit availability announcements.
