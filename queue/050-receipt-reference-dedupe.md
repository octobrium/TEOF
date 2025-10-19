# Task: Deduplicate receipt references across backlog surfaces
Goal: collapse duplicate artifact lists so plans stay the single source while backlog entries and reports link back without repeating payloads.
Notes: audit `_plans/next-development.todo.json`, plan receipts, and `_report/usage/` emitters; introduce pointers (plan id, hash) instead of copied arrays.
Coordinate: S5:L5
Systemic Targets: S5 Intelligence, S6 Truth
Layer Targets: L5 Workflow
Sunset: once backlog entries reference plan receipts indirectly and CI guards enforce the slimmer format.
Fallback: tolerate duplicated lists in backlog, accepting the maintenance overhead.
