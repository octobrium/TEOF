<!-- markdownlint-disable MD013 -->
Status: Normative
Role: Canonical
Purpose: Bind automation to the observation canon; ensure bots, scripts, and adapters execute workflow receipts without eroding governance.
Change process: PR + 2 maintainers (one core)
Review cadence: Quarterly

# L6 – Automation Canon (v1.0)

## Core duties
- **Receipt supremacy:** every automated action must emit an auditable receipt stored under `_report/`, cite the plan/anchor it serves, and pass `scripts/ci` guards where applicable.
- **Guard parity:** automation must exercise the same checks humans run (`teof brief`, `scripts/ci/check_vdp.py`, `tools/doctor.sh`, `pytest …`) and capture the logs as JSON receipts.
- **Escalation discipline:** when guardrails fail or ambiguity surfaces, the bot halts, files a plan update, and publishes a `bus_event --event alert` referencing the blocking receipt.

## External intake policy (v0.1)
Automation may ingest external observations (APIs, crawlers, models) only through a signed receipt envelope:
1. **Canonical schema:** the adapter writes UTF-8 JSON with these minimum fields:
   - `feed_id` (string, lowercase slug)
   - `issued_at` (ISO8601 UTC)
   - `observations` (list of objects with `label`, `value`, `timestamp_utc`, `source`, `volatile`, `stale_labeled`)
   - `hash_sha256` (hex digest of the canonicalized payload body)
   - `signature` (base64url; see below)
   - `public_key_id` (string referencing registered key)
2. **Directory layout:** receipts live under `_report/external/<feed_id>/<issued_at>.json`; adapters may stage raw fetches elsewhere but only signed envelopes enter `_report/external/`.
3. **Plan linkage:** every adapter run must cite an active `_plans/*` step and record that plan id in the envelope metadata (e.g., `plan_id`).
4. **Replay budget:** external receipts older than 24 hours require a manual sunset note in the consuming plan; automation must refuse to act on stale unsigned data.

## Signature scheme (v0.1)
- Default algorithm: **Ed25519** over the canonicalized JSON body (`observations` array plus metadata excluding signature fields).  
- Canonicalization: sort object keys lexicographically, render with `ensure_ascii=False`, no trailing spaces, newline appended.  
- `hash_sha256` is computed over the canonical body; the Ed25519 signature signs the same bytes.  
- Public keys are registered under `governance/keys/<key_id>.pub` with an anchors event linking the key to a steward.  
- Revocation requires: (1) anchors entry, (2) plan documenting replacement, (3) removal of the key from active adapters.

## Verification hooks
- `scripts/ci/check_vdp.py` MUST be extended to verify `_report/external/**` envelopes ( hash + signature + freshness ).  
- `tools/doctor.sh` runs the same verification and fails fast on unsigned receipts.  
- The automation bindings table (`governance/core/L4 - architecture/bindings.yml`) must track coverage for the “Authenticated External Feeds” property.

## Governance obligations
- No adapter ships without an anchors event documenting: feed purpose, steward, key id, retention window, and rollback plan.  
- Every external feed run must write to the coordination bus (`bus_event --event external_feed`).  
- Missing or invalid signatures trigger an immediate `alert` event and block downstream automation until resolved.

## Roadmap (informative)
- v0.2: multi-signature receipts + optional Merkle bundles for high-volume feeds.
- v0.3: third-party audit hooks that mirror receipts to an append-only log.

Automation inherits observation’s contract: **no signature, no action.**
