# Task: Guard bus_message with claims
Goal: require an active claim before emitting bus messages that mutate task state, mirroring bus_event safeguards.
Notes: reuse `_bus/claims` helper, cover terminal states, refresh docs/tests.
Coordinate: S3:L5
Systemic Targets: S3 Propagation, S5 Intelligence, S6 Truth
Layer Targets: L5 Workflow
Sunset: review after automation V2 lands.
Fallback: instruct agents to rely solely on bus_event for guarded updates.
