#!/usr/bin/env bash
# macOS double-click wrapper; calls scripts/freeze.sh and pauses for visibility
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here/.."
bash scripts/freeze.sh "$@"
read -r -p "Press Return to close..." _ || true
