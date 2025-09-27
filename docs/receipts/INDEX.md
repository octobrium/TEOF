# Receipt Index

| Timestamp (UTC)       | Type                  | Verdict | Path                                              | Notes |
|-----------------------|-----------------------|---------|---------------------------------------------------|-------|
| 2025-09-26T20:33:11Z  | Manual verification   | PASS    | docs/receipts/manual-verification/20250926T203311Z | Guardrails spot-check (pre-script) |
| 2025-09-26T21:32:19Z  | Automated attestation | PASS    | docs/receipts/attest/20250926T213219Z               | Full scaffold verification via `scripts/attest_scaffold.py` |
| 2025-09-26T21:43:26Z  | Automated attestation | PASS    | docs/receipts/attest/20250926T214326Z               | Attestation with ethics guard satisfied |
| 2025-09-26T21:45:58Z | Automated attestation  | PASS   | docs/receipts/attest/20250926T214558Z              | Automated attestation |

## Receipt dashboard

Run `python3 -m tools.receipts.main status` to see a pass/fail summary grouped by receipt type.
Add `--format json` for machine-readable output or pass kinds (e.g. `attest`) to scope the scan.

Example:

```bash
python3 -m tools.receipts.main status
```

```
Overall status: PASS
Kind   | Total | Pass | Fail | Latest (UTC)         | Verdict | Path                                                           
------ | ----- | ---- | ---- | -------------------- | ------- | ---------------------------------------------------------------
attest | 3     | 3    | 0    | 2025-09-26T21:45:58Z | PASS    | docs/receipts/attest/20250926T214558Z/receipt.json             
manual | 1     | 1    | 0    | 2025-09-26T20:33:11Z | PASS    | docs/receipts/manual-verification/20250926T203311Z/receipt.json
```
