# Task: BTC Wallet Propagation Loop
Goal: execute PLAN-2025-11-11-btc-wallet-propagation to build the propagation runner, receipts, and CTA/ledger telemetry so BTC inflow is observable.
Notes: blueprint captured in `docs/impact/btc-wallet-propagation-loop.md`; next deliverables are CLI scaffolding, CTA refresh, ledger summary.
Coordinate: S3:S2 / L4
Systemic Targets: S3 Propagation, S2 Energy, S6 Truth
Layer Targets: L4 Architecture, L5 Workflow
Sunset: runner + receipts merged, manager-report referencing propagation metrics, ledger summary live.
Fallback: keep BTC capture strategy aspirational with no instrumentation; wallet stays empty.
