# 2025-09-21-session-sync — Justification

## Objective
Ensure every session starts on the latest commit by automating repo sync (`git fetch --prune && git pull --ff-only`) inside `session_boot` (or companion helper).

## Success Criteria
- Sync helper implemented and documented in onboarding.
- Tests/receipts proving the helper runs safely (no dirty tree, handles failure gracefully).
- Adoption instructions logged in manager report / docs.
