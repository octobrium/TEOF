# TEOF BTC Ledger Contract

Status: Advisory  
Related plan: `_plans/2025-10-06-teof-btc-scoreboard.plan.json`

## Purpose

Keep the TEOF Bitcoin wallet (`docs/impact/teof-btc-wallet.md`) auditable by
recording every donation and disbursement as an observation-backed receipt.

## Receipt shape

Entries live under `_report/impact/btc-ledger/` as append-only JSON files with
the following structure:

```json
{
  "version": 1,
  "wallet": "bc1qxfg8m5tttz5u860f0j7cyhupgdcz25jku44s9c",
  "generated_at": "2025-10-07T00:00:00Z",
  "entries": [
    {
      "txid": "<bitcoin_transaction_id>",
      "direction": "in" | "out",
      "amount_btc": "0.01000000",
      "observed_at": "2025-10-07T00:00:00Z",
      "block_height": 0,
      "evidence": [
        "_report/impact/btc-ledger/proof/<filename>.json",
        "docs/... (optional human narrative)"
      ],
      "linked_work": [
        "_plans/<plan_id>.plan.json",
        "_report/<path-to-corresponding-receipt>"
      ],
      "notes": "Short description (<=160 chars)"
    }
  ],
  "receipt_sha256": "<filled automatically>"
}
```

- `direction` distinguishes inflow (`in`) from disbursement (`out`).
- `amount_btc` uses 8 decimal places as a string to avoid floating errors.
- `evidence` lists immutable artefacts (transaction proof, signed message, etc.).
- `linked_work` ties the movement of funds to observable initiatives.
- `receipt_sha256` is appended by `tools.autonomy.shared.write_receipt_payload`.

## Workflow

1. Capture the raw transaction data (`txid`, `amount`, `block_height`).
2. Generate supporting evidence (JSON pulled from a block explorer, signed message, etc.).
3. Use `python -m tools.impact.btc_record --ledger <path> ...` to append the entry (handles checksum).
4. Store proof material under `_report/impact/btc-ledger/proof/`.
5. Reference the ledger receipt in relevant plans, reports, or dashboards.

All changes must be monotonic. Use new files or append to the end of existing
`entries` arrays; do not rewrite earlier transactions.

## Downstream surfaces

- Dashboards and status reports MAY ingest `_report/impact/btc-ledger/*.json`
  to show cumulative totals, inflow/outflow timelines, and plan linkage.
- Consensus or governance updates MUST cite these receipts when BTC funds are
  part of the decision.

## Next steps

- Automate ledger extraction and dashboard generation (see plan step `step-3`).
- Capture the first on-chain transaction proof under `_report/impact/btc-ledger/proof/`.
