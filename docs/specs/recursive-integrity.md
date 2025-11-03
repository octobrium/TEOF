<!-- markdownlint-disable MD013 -->
# Recursive Integrity Spec v0.1

status: Draft
summary: Defines the systemic verification loop that keeps TEOF releases reproducible and auditable.

**Purpose.** Codify the verification layer that keeps TEOF provable across hosts. The spec distils the legacy "Systems of Alignment & Verification" blueprint into actionable checks that match the current repo’s tooling.

---

## 1. Scope & Guarantees

A system declares compliance when every release, plan, and automation path can be reproduced from:
- the canonical capsule (`capsule/v*/` + `governance/anchors.json`),
- append-only governance events,
- deterministic systemic receipts under `artifacts/`, and
- CI guardrails that enforce policy, coherence, and receipts.

The spec assumes Python ≥3.9 and no hidden network dependencies.

---

## 2. Structural Anchors

| Anchor | Evidence | Check |
| --- | --- | --- |
| **Origin Signature** | `capsule/v1.6/capsule.txt`, `governance/anchors.json`, TAP key `bc1qxfg8m5tttz5u860f0j7cyhupgdcz25jku44s9c` | `scripts/ci/check_hashes.sh` + anchor audit proves the capsule lineage. |
| **Append-only Governance** | `governance/anchors.json` & `governance/keys/` | `scripts/ci/check_append_only.sh origin/main` blocks retroactive edits. |
| **Deterministic Bootloader** | `teof/bootloader.py`, quickstart receipts | `scripts/ci/quickstart_smoke.sh` installs editable package and verifies `artifacts/systemic_out/latest/brief.json`. |
| **Policy Surface** | `scripts/ci/policy_checks.sh`, `.github/workflows/guardrails.yml` | Prevents kernel imports from `experimental/`, `archive/`, `legacy`. |
| **Consensus Receipts** | `artifacts/consensus/ci-*.jsonl` | Guardrail uploads ensure agreement between scorer, planner, and receipts. |

Additional mirrors **must** keep byte-identical copies of `capsule.txt`, `hashes.json`, and `docs/whitepaper.md` to satisfy the distributed mirror clause from the legacy protocol.

---

## 3. Recursive Verification Loop

1. **Observe** – Capture receipts for every automation path.
   - `python -m tools.agent.session_boot` emits bus heartbeats.
   - `_report/usage/**/*` summarises runs for managers.
2. **Cohere** – Run CI guardrails locally (`just guardrails` or `scripts/ci/…`) before pushing.
3. **Ethics** – `scripts/policy_checks.sh` enforces the canonical covenant: high-leverage modules cannot depend on unreviewed experiments.
4. **Reproduce** – `teof brief` regenerates receipts; compare with previous `artifacts/systemic_out/<STAMP>/` using `scripts/ci/check_consensus_receipts.py`.
5. **Self-repair** – On contradiction, open a plan under `_plans/` and log the delta on `_bus/events/events.jsonl`.

This loop operationalises the systemic readiness cycle described in the whitepaper (§2.1).

---

## 4. Fractal Audit (10 Questions)

Use the checklist across layers and agents. Failure on any item requires receipts and a recovery plan.

1. **Unity** – Does the work point to a single capsule + anchor? (`capsule/current` symlink)  
2. **Energy** – Are transformations logged with receipts timestamps? (`artifacts/systemic_out/`)  
3. **Propagation** – Can another host replay the change from hashes + receipts?  
4. **Resilience** – Did guardrails run and pass? (CI badge, local run log)  
5. **Intelligence** – Were contradictions resolved via `_plans/` or `_bus/` updates?  
6. **Truth** – Are assertions backed by consensus or tests? (`tests/**`, `_report/usage/manager-report.md`)  
7. **Power** – Does new automation respect policy boundaries? (imports, budget caps)  
8. **Ethics** – Did the change expand observation options instead of locking them down?  
9. **Freedom** – Can peers fork or exit without losing receipts? (mirrors, exported bundles)  
10. **Meaning** – Does the narrative in manager reports increase clarity? (`_report/usage/manager-report.md`)

The first six questions are mandatory for every PR. Items 7–10 apply to governance and automation promotions.

---

## 5. Execution Playbook

| Stage | Owner | Command / Artifact |
| --- | --- | --- |
| Local preflight | Agent | `scripts/policy_checks.sh`, `python -m tools.agent.bus_watch --follow` |
| Capsule freeze | Steward | `scripts/freeze.sh` → update `governance/anchors.json` |
| Receipt review | Manager | `_report/usage/manager-report.md` + attachments |
| External mirror | Infra | Sync `capsule/`, `docs/`, `governance/` to cold storage; verify hash match |

Deviation requires a logged crisis plan anchored to systemic axis `S1 Observation` or higher.

---

## 6. References

- Legacy *Section 9 — Systems of Alignment and Verification* (Infodump “Meat 1”)  
- TAP Protocol (§Final Affirmation, `docs/foundation/alignment-protocol/tap.md`)  
- Guardrails workflow (`.github/workflows/guardrails.yml`)  
- Consensus tooling (`scripts/ci/consensus_smoke.sh`, `scripts/ci/check_consensus_receipts.py`)
