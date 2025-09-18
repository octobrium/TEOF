# Task: Align task_assign with bus_message
Goal: refactor `tools/agent/task_assign` to reuse the bus_message helper so assignments stay consistent.
Notes: adjust CLI output, update tests to cover assignment payloads, and document the workflow.
OCERS Target: Coherence↑ Evidence↑
Sunset: revisit if task_assign merges into a consolidated manager CLI.
Fallback: keep manual JSON writes.
