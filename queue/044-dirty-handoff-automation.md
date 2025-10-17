# Task: Dirty Worktree Handoff Automation
Goal: surface guardrails when a session picks up a repo with existing uncommitted changes so the new agent knows how to proceed without manual escalation.
Notes: hook into `session_boot` (or a helper) to emit a structured receipt + bus status note when sync aborts on dirty trees, optionally nudging the agent to log the finding. Explore lightweight alerts in coord_dashboard so idle agents see outstanding dirty handoffs.
Coordinate: S3:L5
Systemic Targets: S1 Unity, S2 Energy, S3 Propagation, S6 Truth
Layer Targets: L5 Workflow
Sunset: when the automation lands and onboarding references the new guard.
Fallback: rely on the parallel-codex doc guidance and manual bus_event logging.
