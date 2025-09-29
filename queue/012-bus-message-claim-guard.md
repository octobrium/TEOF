# Task: Guard bus_message with claims
Goal: require an active claim before emitting bus messages that mutate task state, mirroring bus_event safeguards.
Notes: reuse `_bus/claims` helper, cover terminal states, refresh docs/tests.
OCERS Target: Coherence↑ Reproducibility↑
Coordinate: S3:L5
Sunset: review after automation V2 lands.
Fallback: instruct agents to rely solely on bus_event for guarded updates.
