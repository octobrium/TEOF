# Design log — repo hygiene (codex-4)

Directive: BUS-COORD-0004 assigns codex-4 to finalize the bus/session_boot/heartbeat helpers before the next push. Steps:
- Review outstanding diffs touching `tools/agent/bus_event.py`, `tools/agent/bus_message.py`, `tools/agent/session_boot.py`, and new heartbeat helper to confirm they align with the heartbeat integration plan.
- Re-run targeted pytest suites for bus helpers and session bootstrap (`tests/test_agent_bus_message.py`, `tests/test_manifest_helper.py`, `tests/test_session_boot.py`, `tests/test_agent_heartbeat.py`).
- Log receipts + status back on BUS-COORD-0004 so codex-1 knows the surface is ready.
