# Conductor Agent Pilot Ideas

Tracking candidate experiments for ND-009 (“External agent pilot”). Each idea
assumes conductor remains the policy surface and receipts backbone.

Each pilot must honour L3 properties (P1–P6). Preflight checklist:
1. Verify authenticity + consent status; abort on failure.
2. Reference the parent objective (O1–O7) in receipts.
3. Emit a metabolite (reflection stub or backlog update) after the cycle.

## 1. UI Macro Loop (Local Sandbox)
- **Goal:** prove end-to-end prompt consumption by driving the Codex CLI with
  macOS `osascript` / Linux `xdotool` while honouring consent flags.
- **Safeguards:**
  - Preflight consent + authenticity (P2) before each injection.
  - Log macro actions to `_report/usage/autonomy-conductor/ui-macro-*.json`
    including operator identity (P4).
- **Metabolite:** reflection intake record summarising human review outcome.
- **Deliverables:** shell script + README; demo receipt with prompt and executed
  keystrokes.

## 2. API Relay Agent
- **Goal:** consume conductor receipts and send prompts to the OpenAI API (or
  another hosted model), capturing the response as a new receipt.
- **Safeguards:**
  - Mask secrets with `.env`; do not commit API keys.
  - Record the full exchange under `_report/usage/autonomy-conductor/api-relay/`
    with referenced objective (P1) and diff/test verification (P6).
  - Enforce guardrail diff/test caps before applying commands.
- **Metabolite:** backlog snippet outlining the returned plan or command batch.
- **Deliverables:** Python CLI (`tools/autonomy/agent_relay.py`), tests, pilot
  run receipt, and reflection follow-up.
  - **Pilot receipt:** `_report/usage/autonomy-conductor/conductor-20250923T204918Z.json`
    → `_report/usage/autonomy-conductor/api-relay/relay-conductor-20250923T204918Z.json`
    with metabolite `_report/usage/autonomy-conductor/api-relay/metabolites/metabolite-relay-conductor-20250923T204918Z.json`
    and reflection `memory/reflections/reflection-20250923T205003Z.json`.

## 3. Local LLM Co-pilot
- **Goal:** run a lightweight local model (e.g., llama.cpp) that ingests
  conductor prompts and proposes command batches offline.
- **Safeguards:**
  - Snapshot model hash / version in the receipt.
  - Rate-limit to prevent runaway loops.
  - Compare proposed commands to diff limit; truncate if necessary.
- **Metabolite:** comparison reflection capturing local model behaviour vs.
  objectives (P3).
- **Deliverables:** integration notes, configuration example, recorded pilot run.

## 4. Human-in-the-Loop Review Queue
- **Goal:** push conductor prompts into a simple web UI (or markdown inbox) so a
  human reviewer can approve/refine before handing back to Codex.
- **Safeguards:**
  - Require explicit acknowledgement per prompt.
  - Stamp reviewer identity + decision in `_report/usage/autonomy-conductor/hil/`.
- **Metabolite:** reviewer-signed reflection or backlog update explaining the
  decision (P3/P4).
- **Deliverables:** minimal UI or CLI, plus governance note for reviewer role.

## 5. Guardrail Regression Harness
- **Goal:** replay recorded prompts/responses to verify future guardrail
  changes don’t break the loop.
- **Safeguards:**
  - Store fixtures under `tests/data/autonomy-conductor/`.
  - Add pytest coverage ensuring diff/test caps remain enforced when replaying.
- **Metabolite:** regression report linking results to objectives (e.g., O5/O6).
- **Deliverables:** fixture set + regression test.

---

For each idea, log work as receipts tied to plan `2025-09-23-autonomy-roadmap`
to maintain provenance.
