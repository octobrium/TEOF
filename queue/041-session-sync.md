# Task: Session Sync Helper
Goal: add a deterministic `git fetch --prune && git pull --ff-only` helper (integrated with `session_boot` or standalone) so every session starts on the latest commit automatically.
Notes: prevents stale manager directives during pickup; run before heartbeat watcher and scaffolding.
OCERS Target: Observation↑ Coherence↑
Sunset: when the helper ships and agents adopt it in onboarding.
Fallback: remind agents manually via onboarding doc.
