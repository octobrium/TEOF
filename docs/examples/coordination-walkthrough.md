# Agent Coordination Walkthrough

**Scenario**: Two AI agents (codex-3 and codex-4) coordinating to implement a new feature—adding a `health_check` endpoint to a service.

This walkthrough shows actual TEOF commands, generated receipts, and coordination flow.

---

## Setup: Agent Identities

Each agent has a manifest in the repository root:

**AGENT_MANIFEST.json** (codex-4):
```json
{
  "agent_id": "codex-4",
  "role": "backend-engineer",
  "branch_prefix": "agent/codex-4",
  "created_at": "2025-01-07T10:00:00Z"
}
```

---

## Step 1: Agent Announces Presence

**codex-4 starts session:**
```bash
$ python -m tools.agent.session_boot --agent codex-4 --focus backend --with-status

✓ Synced repository (git fetch && git pull)
✓ Recorded handshake in _bus/events/events.jsonl
✓ Captured bus status snapshot in _report/agent/codex-4/session_boot/
✓ Captured manager-report tail in _report/session/codex-4/manager-report-tail.txt

Session started: codex-4 (focus: backend)
```

**Generated event** (`_bus/events/events.jsonl`, appended):
```json
{"ts":"2025-01-07T10:05:12Z","agent_id":"codex-4","event":"handshake","focus":"backend","branch":"main"}
```

---

## Step 2: Manager Assigns Task

A human manager (or manager agent) sees the task in the backlog and assigns it:

```bash
$ python -m tools.agent.task_assign --task QUEUE-042 --agent codex-4 \
    --summary "Add health check endpoint" --plan 2025-01-07-health-check
```

**Generated claim** (`_bus/claims/QUEUE-042.json`):
```json
{
  "task_id": "QUEUE-042",
  "plan_id": "2025-01-07-health-check",
  "agent_id": "codex-4",
  "branch": "agent/codex-4/health-check",
  "claimed_at": "2025-01-07T10:06:00Z",
  "status": "active",
  "notes": "Implement /health endpoint with dependency checks"
}
```

**Generated message** (`_bus/messages/QUEUE-042.jsonl`, appended):
```json
{"ts":"2025-01-07T10:06:00Z","type":"assignment","agent_id":"manager","summary":"Assigned QUEUE-042 to codex-4","plan_id":"2025-01-07-health-check"}
```

---

## Step 3: Agent Starts Work

**codex-4 acknowledges and starts:**
```bash
$ python -m tools.agent.bus_event log --event status --task QUEUE-042 \
    --summary "codex-4: starting health check implementation"

✓ Event logged to _bus/events/events.jsonl
```

**Generated event**:
```json
{"ts":"2025-01-07T10:07:30Z","agent_id":"codex-4","event":"status","task_id":"QUEUE-042","summary":"codex-4: starting health check implementation"}
```

**codex-4 creates branch and implements the feature:**
```bash
$ git checkout -b agent/codex-4/health-check
# ... writes code ...
$ git add src/api/health.py tests/test_health.py
$ git commit -m "feat: add health check endpoint with DB/cache checks"
```

---

## Step 4: Agent Emits Progress Receipt

**codex-4 logs test results:**
```bash
$ pytest tests/test_health.py > _report/agent/codex-4/QUEUE-042/test-results.txt
$ python -m tools.agent.bus_message --task QUEUE-042 --type status \
    --summary "codex-4: tests passing (5/5)" \
    --receipt _report/agent/codex-4/QUEUE-042/test-results.txt

✓ Message posted to _bus/messages/QUEUE-042.jsonl
```

**Generated message**:
```json
{"ts":"2025-01-07T10:15:20Z","type":"status","agent_id":"codex-4","task_id":"QUEUE-042","summary":"codex-4: tests passing (5/5)","receipts":["_report/agent/codex-4/QUEUE-042/test-results.txt"]}
```

---

## Step 5: Another Agent Reviews (Optional)

**codex-3 (reviewer role) monitors the bus:**
```bash
$ python -m tools.agent.bus_watch --task QUEUE-042 --follow

[2025-01-07T10:06:00Z] assignment | manager: Assigned QUEUE-042 to codex-4
[2025-01-07T10:07:30Z] status | codex-4: starting health check implementation
[2025-01-07T10:15:20Z] status | codex-4: tests passing (5/5)
```

**codex-3 reviews and comments:**
```bash
$ python -m tools.agent.bus_message --task QUEUE-042 --type review \
    --summary "codex-3: LGTM, consider adding timeout param" \
    --meta reviewer=codex-3

✓ Message posted
```

---

## Step 6: Agent Completes Work

**codex-4 addresses feedback and opens PR:**
```bash
$ git add src/api/health.py
$ git commit -m "feat: add timeout parameter to health check"
$ git push origin agent/codex-4/health-check
$ gh pr create --title "Add health check endpoint" --body "Closes QUEUE-042..."

✓ PR #156 created
```

**codex-4 logs completion:**
```bash
$ python -m tools.agent.bus_event log --event pr_opened --task QUEUE-042 \
    --summary "codex-4: PR #156 opened" --meta pr=156

$ python -m tools.agent.bus_claim release --task QUEUE-042 --status done \
    --summary "Implementation complete, tests green, PR opened"

✓ Claim released
✓ Status updated to 'done' in _bus/claims/QUEUE-042.json
```

**Updated claim** (`_bus/claims/QUEUE-042.json`):
```json
{
  "task_id": "QUEUE-042",
  "plan_id": "2025-01-07-health-check",
  "agent_id": "codex-4",
  "branch": "agent/codex-4/health-check",
  "claimed_at": "2025-01-07T10:06:00Z",
  "released_at": "2025-01-07T10:25:00Z",
  "status": "done",
  "notes": "Implementation complete, tests green, PR opened"
}
```

---

## Step 7: Memory Log Entry

**codex-4 records the decision in memory:**
```bash
$ python tools/memory/log-entry.py \
    --summary "Implemented health check endpoint with DB and cache checks" \
    --ref QUEUE-042 \
    --artifact _report/agent/codex-4/QUEUE-042/test-results.txt \
    --artifact _bus/claims/QUEUE-042.json

✓ Memory entry appended to memory/log.jsonl
```

**Memory entry** (`memory/log.jsonl`, appended):
```json
{
  "ts": "2025-01-07T10:26:00Z",
  "actor": "codex-4",
  "summary": "Implemented health check endpoint with DB and cache checks",
  "ref": "QUEUE-042",
  "artifacts": [
    "_report/agent/codex-4/QUEUE-042/test-results.txt",
    "_bus/claims/QUEUE-042.json"
  ],
  "hash_prev": "d864891fc56f5daf615fadf199ffdda2dcc9c286fa489f3c81a295535c0d46e9",
  "hash_self": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
}
```

---

## What Just Happened (Summary)

1. **Agent identity** — codex-4 has a manifest declaring its ID and role
2. **Session handshake** — agent announces presence on the bus
3. **Task assignment** — manager assigns work, creating a claim
4. **Coordination** — agent emits status updates visible to other agents
5. **Review** — another agent (codex-3) reviews and comments via the bus
6. **Completion** — agent releases claim, logs to memory
7. **Auditability** — every step generated receipts:
   - `_bus/events/events.jsonl` — timeline of events
   - `_bus/claims/QUEUE-042.json` — ownership record
   - `_bus/messages/QUEUE-042.jsonl` — task-specific communication
   - `_report/agent/codex-4/QUEUE-042/` — test results and artifacts
   - `memory/log.jsonl` — decision provenance with hash chain

---

## Key Insights

**No external infrastructure**: All coordination happened through git-versioned files. No Redis, no message queue, no database.

**Fully auditable**: You can trace exactly:
- Who worked on what (`_bus/claims/`)
- What they did (`_bus/events/`, git commits)
- Why they did it (`memory/log.jsonl`)
- What the results were (`_report/`)

**Reversible**: If the health check implementation has a bug:
1. Check `memory/log.jsonl` to find when it was introduced
2. Check `_bus/events/` to see which agent did it
3. Check `_report/agent/codex-4/QUEUE-042/` to see what tests passed
4. Revert the PR and investigate with full context

**Inherited context**: When codex-5 starts a new session tomorrow, it reads:
- `memory/log.jsonl` — sees the health check was added
- `_bus/claims/` — sees codex-4 completed QUEUE-042
- `_report/` — has access to all test receipts
- No need to ask "what happened" — the receipts tell the story

---

## Next Steps

- **Run the example yourself**: See [docs/onboarding/tier1-evaluate-PROTOTYPE.md](../onboarding/tier1-evaluate-PROTOTYPE.md)
- **Understand the architecture**: Read [docs/architecture.md](../architecture.md)
- **Integrate your own agents**: See [docs/agents.md](../agents.md)
