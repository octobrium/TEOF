# Agent Proposal Justification

## Why this helps
`anchors.json` guards currently allow reordering, creating gaps in the append-only history. The queue task QUEUE-000 asks us to require each new anchor event to append with a matching `prev_content_hash`, reducing tampering risk.

## Proposed change
Introduce validation so anchor writes must match the most recent `content_hash` and reject insertions mid-history. Update any helper code and documentation to describe the stricter policy.

## Receipts to collect
- `_report/agent/codex-2/anchors-append-guard/pytest.json`
- `_report/agent/codex-2/anchors-append-guard/lint.json` (if lint runs)

## Tests / verification
- `pytest tests/anchors` (TODO)
- `pytest` (TODO)

## Ethics & safety notes
None.
