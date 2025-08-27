# Task: Anchors append-only guard
Goal: Add a fast guard so new `governance/anchors.json` events must:
- append at the end (no mid-file edits),
- include `prev_content_hash`,
- have non-decreasing `ts`.
OCERS Target: Evidence↑ Safety↑ Coherence↑
Sunset: Remove if it creates false positives >5% of PRs for two weeks.
Fallback: Keep warn-only in doctor and manual review of anchors.
Acceptance: `tools/doctor.sh` shows no ❌ for valid append; fails on mid-file edits.
