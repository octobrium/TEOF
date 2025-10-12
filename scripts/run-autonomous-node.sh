#!/usr/bin/env bash
# Run the TEOF autonomous node workflow once.
# Intended for cron/systemd timers or manual execution.
set -eo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m tools.autonomy.node_runner --limit "${1:-10}" --dest "$REPO_DIR/docs/usage/autonomous-node"
