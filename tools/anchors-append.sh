#!/usr/bin/env bash
set -euo pipefail
EVENT="${1:?usage: tools/anchors-append.sh _report/anchors/new_event.vX.Y.json}"
scripts/ci/anchors_append.py "$EVENT"
git add governance/anchors.json
git commit -m "governance: append anchors event from $(basename "$EVENT")" || true
tools/doctor.sh
