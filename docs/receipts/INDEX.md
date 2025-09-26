# Receipt Index

| Timestamp (UTC)       | Type                  | Verdict | Path                                              | Notes |
|-----------------------|-----------------------|---------|---------------------------------------------------|-------|
| 2025-09-26T20:33:11Z  | Manual verification   | PASS    | docs/receipts/manual-verification/20250926T203311Z | Guardrails spot-check (pre-script) |
| 2025-09-26T21:32:19Z  | Automated attestation | PASS    | docs/receipts/attest/20250926T213219Z               | Full scaffold verification via `scripts/attest_scaffold.py` |
| 2025-09-26T21:41:22Z  | Automated attestation | FAIL    | docs/receipts/attest/20250926T214122Z               | Negative control: ethics guard flagged missing consent |
| 2025-09-26T21:43:26Z  | Automated attestation | PASS    | docs/receipts/attest/20250926T214326Z               | Attestation with ethics guard satisfied |
| 2025-09-26T21:45:58Z | Automated attestation  | PASS   | docs/receipts/attest/20250926T214558Z              | Automated attestation |
