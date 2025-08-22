#!/usr/bin/env bash
set -euo pipefail

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTDIR="ocers_out/${STAMP}"
mkdir -p "$OUTDIR"

REPORT="${OUTDIR}/brief.json"

cat > "$REPORT" <<'JSON'
{
  "ocers": {
    "observation": "Daily market brief (stub).",
    "coherence": "",
    "evidence": "",
    "result": "Caution on ETF premium/discount; BTC medium-term constructive.",
    "scope": "Tactical (days-weeks)."
  },
  "observations": [
    {
      "label": "BTC last",
      "value": null,
      "timestamp_utc": null,
      "source": null,
      "volatile": true,
      "stale_labeled": false
    },
    {
      "label": "IBIT last",
      "value": null,
      "timestamp_utc": null,
      "source": null,
      "volatile": true,
      "stale_labeled": false
    },
    {
      "label": "NVDA last",
      "value": null,
      "timestamp_utc": null,
      "source": null,
      "volatile": true,
      "stale_labeled": false
    }
  ]
}
JSON

TEOF_MODE="${TEOF_MODE:-explore}" python3 tools/teof_evaluator.py < "$REPORT" | tee "${OUTDIR}/score.txt"

echo "wrote ${OUTDIR}"
