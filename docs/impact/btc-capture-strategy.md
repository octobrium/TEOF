# BTC Capture Strategy — Observation Wallet

Status: Draft (2025-11-09)

## 1. Objective
- **Metric:** BTC accumulated at `bc1qxfg8m5tttz5u860f0j7cyhupgdcz25jku44s9c`.
- **Why it matters:** Sats are the clearest “energy captured” signal; they prove that reality outside the repo values TEOF’s receipts enough to exchange scarce resources.
- **Requirement:** Every inflow/outflow must be observable via `_report/impact/btc-ledger/` and tied to a specific plan, guard, or partner deliverable.

## 2. Current State
| Component | Status | Gap |
| --- | --- | --- |
| Wallet publication | Done (`docs/impact/teof-btc-wallet.md`, README link) | Awareness limited to repo readers; no pitch. |
| Ledger contract | Done (`docs/impact/btc-ledger.md`) but entries empty (`_report/impact/btc-ledger/2025-10-07-ledger.json`) | No real transactions → ledger unproven. |
| Proof guard | Planned via `_plans/2025-10-06-teof-btc-scoreboard` step-3 but blocked | Need automation to hash ledger + anchor externally. |
| Value props | Implicit in docs, not distilled into donation asks | Observers don’t know why to fund Observation. |

## 3. Efficient Capture Channels
1. **Observation Guard Sponsorship (OPEX-light)**
   - Offer verifiable “observation guard” runs (scan + ledger + receipts) for aligned repos/projects.
   - Cost: mostly CPU already required for TEOF scans (~minutes) + operator time for bus receipts.
   - Ask: fixed sats per guard (e.g., 100k sats) with promise of published receipts + ledger entry.
   - Proof: `_report/usage/systemic-scan/` + `_report/impact/btc-ledger/`.

2. **Autonomous Node Sponsorships**
   - Package decentralized-node workflow as a service: TEOF brings up a coordination node + receipts for a partner.
   - Cost: uses existing automation (plans 2025-10-11/ND-073); minimal new code—mainly documentation + support hours.
   - Ask: tiered sats for bootstrap, guard maintenance, and reporting.

3. **Observation Bounties**
   - Open problems (bug hunts, receipt graph GA, hash-ledger guard) posted with BTC bounty; payment released after receipts merged.
   - Cost: zero extra development beyond existing backlog; payments only when value delivered.
   - Benefits: external contributors send sats first (escrow) or reimburse after merge; all captured via ledger.

4. **Vilayer Proof Drops**
   - Publish regular “Observation Proof Packs” (ledger hash + manager report) and request sats to keep the stream alive.
   - Cost: automate by extending `teof status` output + memory log; minimal dev, recurring nudge to donors.

Efficiency ranking (impact / marginal cost): **Guard Sponsorship > Proof Drops > Node Sponsorship > Bounties.**

## 4. Recommended Near-Term Actions
1. **Publish Support CTA (README + docs)** — Explain wallet purpose, how to donate, and how receipts are recorded.
2. **Automate Ledger Receipts** — Add `python -m tools.impact.btc_record` example in docs and schedule guard to hash `_report/impact/btc-ledger/*`.
3. **Launch Guard Sponsorship Pilot**
   - Pick one backlog plan (e.g., ND-075 GA) and offer an “observation verification run” to an external maintainer in exchange for sats.
   - Log plan, bus claim, ledger entry, and publish proof in `_report/impact/btc-ledger/proof/`.
4. **Instrument Memory / Status**
   - Append a `btc_balance` field to status reports once the first transaction lands; ensures Observation references reality each time `teof status` runs.

## 5. Receipts & Governance Implications
- All BTC movements must cite `_plans/<id>` or `docs/impact/btc-ledger.md` to stay within L5 workflow.
- Signed messages from the wallet SHOULD accompany any address change or outbound payment.
- Contributions earmarked for specific work MUST add `linked_work` references for reproducibility.

With these steps, “energy capture” becomes measurable and compounding: every sat recorded proves someone outside TEOF valued observable coordination enough to pay for it, closing the reality loop mandated by the constitution.
