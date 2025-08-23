#!/usr/bin/env bash
# macOS double‑click wrapper; ensures bash and pauses for visibility
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
cd "$script_dir/.."
/usr/bin/env bash scripts/freeze.sh "$@"
read -r -p "Press Return to close..." _ || true
