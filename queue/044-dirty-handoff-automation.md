# Task: Dirty Worktree Handoff Automation
Goal: surface guardrails when a session picks up a repo with existing uncommitted changes so the new agent knows how to proceed without manual escalation.
Notes: hook into `session_boot` (or a helper) to emit a structured receipt + bus status note when sync aborts on dirty trees, optionally nudging the agent to log the finding. Explore lightweight alerts in coord_dashboard so idle agents see outstanding dirty handoffs.
OCERS Target: Observation↑ Coherence↑
Coordinate: S3:L5
Sunset: when the automation lands and onboarding references the new guard.
Fallback: rely on the parallel-codex doc guidance and manual bus_event logging.
