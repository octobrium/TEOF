# Manager Coordination Enhancements

## Why this helps
Running multiple Codex instances required stronger coordination to avoid conflicting work and noisy receipts. Adding an explicit task graph, assignment messages, and manager summaries lets agents self-organize, while CI checks and preflight scripts catch missing receipts early.

## Proposed change
1. Introduce shared task metadata (`agents/tasks/tasks.json`), assignment files (`_bus/assignments/`), and message logs (`_bus/messages/*.jsonl`).
2. Ship manager tooling (`task_assign`, `manager_report`), plus a receipts preflight helper and expanded docs.
3. Tighten CI (`check_agent_bus.py`) and `bus_claim` so engineers need explicit assignments.
4. Enhance `bus_status` filters and add tests to keep visibility high.

## Receipts to collect
- `_report/agent/codex-2/agent-bus-status/pytest.json`
- `_report/manager/manager-report-2025-09-18T02:07:19Z.md`
- `tests/test_agent_bus_claim.py`
- `tests/test_agent_bus_status.py`

## Tests / verification
- `tools/agent/preflight.sh`
- `python3 scripts/ci/check_agent_bus.py`
- `pytest tests/test_agent_bus_claim.py tests/test_agent_bus_status.py`

## Ethics & safety notes
No new external access; coordination artifacts remain inside the repo with auditability.
