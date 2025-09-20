#!/usr/bin/env python3
"""Helpers for logging agent heartbeats via the coordination bus."""
from __future__ import annotations

import argparse
import json
from typing import Dict, Mapping, MutableMapping

from tools.agent import bus_event


def _format_extras(extras: Mapping[str, str] | None) -> list[str]:
    if not extras:
        return []
    formatted: list[str] = []
    for key, value in extras.items():
        key = str(key).strip()
        if not key:
            raise ValueError("heartbeat metadata keys must be non-empty")
        formatted.append(f"{key}={value}")
    return formatted


def emit_status(
    agent_id: str,
    summary: str,
    *,
    extras: Mapping[str, str] | None = None,
    dry_run: bool = False,
) -> MutableMapping[str, object]:
    """Emit a status heartbeat event.

    Args:
        agent_id: The agent emitting the heartbeat.
        summary: Summary text for the status event.
        extras: Optional metadata to append to the event payload.
        dry_run: If True, do not write to the bus; instead print the
            payload that would be logged.

    Returns:
        The payload dictionary that would be recorded.
    """

    payload: MutableMapping[str, object] = {
        "agent_id": agent_id,
        "event": "status",
        "summary": summary,
    }
    if extras:
        payload["extras"] = dict(extras)

    if dry_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return payload

    args = argparse.Namespace(
        agent=agent_id,
        event="status",
        summary=summary,
        task=None,
        plan=None,
        branch=None,
        pr=None,
        receipt=None,
        extra=_format_extras(extras),
        severity=None,
        consensus_decision=None,
        consensus_output=None,
        consensus_meta=None,
    )
    bus_event.handle_log(args)
    return payload


__all__ = ["emit_status"]
