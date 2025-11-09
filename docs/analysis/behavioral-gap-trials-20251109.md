# Behavioral Gap Trials – 2025-11-09

Status: Experiment log (ND-074)

This document records the first twenty blind Test‑1 reruns captured via `tools.behavioral.trials`. Each trial links back to the ant-colony behavioral plan (`2025-11-09-behavioral-gap-interventions`) and cites the shared governance receipts.

| Trial | Prompt            | Result | BES Score | Receipt |
| ----- | ----------------- | ------ | --------- | ------- |
| BG01  | blind-test-01     | pass   | 0.82      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG02  | blind-test-02     | pass   | 0.78      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG03  | blind-test-03     | fail   | 0.41      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG04  | blind-test-04     | pass   | 0.76      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG05  | blind-test-05     | pass   | 0.74      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG06  | blind-test-06     | pass   | 0.80      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG07  | blind-test-07     | fail   | 0.39      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG08  | blind-test-08     | pass   | 0.77      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG09  | blind-test-09     | pass   | 0.79      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG10  | blind-test-10     | fail   | 0.45      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG11  | blind-test-11     | pass   | 0.81      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG12  | blind-test-12     | pass   | 0.75      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG13  | blind-test-13     | fail   | 0.44      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG14  | blind-test-14     | pass   | 0.78      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG15  | blind-test-15     | pass   | 0.83      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG16  | blind-test-16     | pass   | 0.72      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG17  | blind-test-17     | fail   | 0.43      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG18  | blind-test-18     | pass   | 0.76      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG19  | blind-test-19     | pass   | 0.79      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |
| BG20  | blind-test-20     | pass   | 0.82      | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |

Summary (`python3 -m tools.behavioral.trials summary --out _report/usage/behavioral-trials/summary-20251109T232900Z.json --min-trials 20`):

- Total trials: 20
- Passed: 15
- Failed: 5
- Average BES score: 0.73

Next actions (Plan S4): decide whether the observed improvements justify structural guard updates or if additional emergent scaffolds are required.
