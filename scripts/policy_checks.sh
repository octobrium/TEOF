#!/usr/bin/env bash
set -euo pipefail

dirname "${BASH_SOURCE[0]}" >/dev/null 2>&1
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec "$SCRIPT_DIR/ci/policy_checks.sh" "$@"
