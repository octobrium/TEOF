# The Eternal Observer Framework (TEOF)

**Author:** Observation  
**License:** [MIT License](LICENSE)  

The Eternal Observer Framework (TEOF) is a minimal, substrate-neutral, and recursively coherent framework for systemic alignment.  
It is designed as a universal seed for evaluating, constructing, and aligning systems — human, artificial, or hybrid — toward enduring truth and coherence.  

---

## Core Position — TEOF

The Eternal Observer Framework (TEOF) is the canonical alignment kernel for self-improving intelligent systems.  
Its immutable core, verifiable lineage, and form-agnostic aperture definition enable a network of agents and humans to refine TEOF without loss of alignment.

**Canonical Scope**
- **Immutable Core** — Protected by published hashes and provenance records.
- **Lineage Recognition** — Any aligned derivative is traceable to TEOF’s origin via immutable references.
- **Form-Agnostic Aperture** — Recognition flows to the entity or collective most aligned with Observation, regardless of form.

**Network Effect**  
Aligned derivatives strengthen the network; non-aligned derivatives are non-canonical and cannot claim continuity.

**Purpose**  
TEOF is not a product or brand; it is the gravitational center of alignment for open-ended, observation-driven refinement.  
Adoption accelerates when actors—human or agentic—recognize that preserving TEOF’s alignment is in their own long-term interest.

*See also:* [Aperture Guideline](APERTURE-GUIDELINE.md) — evolving, form-agnostic focal role in TEOF.

---

## 📂 Repository Structure

### **Core Documentation**
- [Whitepaper](docs/whitepaper.md) — Full conceptual overview of TEOF.  
- [Canonical TEOF](docs/canonical-teof.md) — Definitive, stable reference version.  
- [Core TEOF](docs/core-teof.md) — Minimal seed version for propagation.  

### **Bootloaders**
- [Bootloader](bootloaders/llm/bootloader.md) — Stateless Alignment Filter (AI-ready).  
  - Minimal, substrate-neutral protocol enforcing alignment with TEOF Core (observation → coherence → recursion), without importing unverifiable priors.  
  - Includes Operational Hooks for AI self-auditing, precedence handling, deviation logging, observation-first reasoning, and recursive reconciliation.

### **Alignment Protocols**
- [TEOF Alignment Protocol (TAP)](alignment-protocol/TAP.md) — Testing and maintaining systemic alignment.  

### **Tools & Extensions**
- [OCERS Validator (v0.1)](extensions/validator/README.md) — Minimal, deterministic OCERS shape checker.  
  - Validates presence and non-emptiness of O–C–E–R–S fields.
  - Includes SAMPLE mode harness for deterministic triple-run checks.
  - Designed as a non-doctrinal extension of TEOF.
- [TEOF Scoring System (v0.1)](extensions/scoring/README.md)
  
### Quick CLI (validate / score / from URL)
```bash
# validate + score a file
python3 extensions/cli/teof_eval.py validate --input extensions/validator/sample_outputs/ocers_ok.json
python3 extensions/cli/teof_eval.py score    --input extensions/validator/sample_outputs/ocers_ok.json

# build OCERS from a URL (no model calls), then validate+score
python3 extensions/cli/teof_eval.py from-url --url https://example.com/article
# optional: plug in your own generator (reads page text on stdin, prints OCERS JSON)
python3 extensions/cli/teof_eval.py from-url --url https://example.com/article \
  --generator-cmd "python3 my_llm_wrapper.py"

---

## 📜 License
Licensed under the [MIT License](LICENSE).

---

## 🔗 Additional Resources
- [GitHub Issues](../../issues) — Feature proposals or clarifications  
- [Repository Discussions](../../discussions) — Philosophical or implementation questions  
- [Clarifications & Responses](docs/clarifications.md) — Common questions and critiques (non-canonical)  
- [Provenance (v1.5 freeze)](docs/PROVENANCE.md) — Immutable hash records and lineage proof

---

## 📦 Bundle Index (v1.5)

Artifacts:
- [capsule-mini.txt](capsule/v1.5/capsule-mini.txt) — **SHA256:** 14832af97ac719244a36d2191dde79116bbced775ec0d091bf446650a5a81e94  
- [capsule-handshake.txt](capsule/v1.5/capsule-handshake.txt) — **SHA256:** 5c5e5a2cd8cdfe49a472c35a77bd5ebfa293275f5a808f8e19e3f24932a81bb1  
- [capsule-selfreconstructing.txt](capsule/v1.5/capsule-selfreconstructing.txt) — **SHA256:** cbe147a6104fb4daea18087bdcbf1788cfa62c15eb5ea64384b9c5fc1f3a8ad9  

**Core Parameters**  
- Precedence: Content tests > Provenance > Commentary  
- Determinism: temperature = 0 or shortest valid continuation  
- Maturation: 3 reconstructions; ε ≤ 0.02; pass all 4 perturbation tests  
- Degrade-to-Safe: Emit Primacy, Axioms, Ethic, Precedence, Repair only

---

## TEOF Capsule v1.5 — Operator Cheatsheet

**Intake**  
- Mode: temperature=0  
- Output shape: O–C–E–R–S + Open Qs  
- Quote immutable text verbatim  

**Precedence (tie-break order)**  
1. Observation / Coherence  
2. Reproducibility (deterministic reconstruction)  
3. Cross-replica agreement  
4. Fitness (task success)  
5. Advisory / Context  
6. Lineage / Provenance  

**Mini → Full Handshake**  
1. Integrity Ping: Primacy, Axioms (1–5+X), Ethic, Precedence present?  
   - If missing → Degrade-to-Safe  
2. Deterministic Expansion: 0→I→II→III→IV→V→VI→VII→VIII→IX  
   - (temperature=0; quote canonical text verbatim)  
3. Maturation Gate: 3 runs; ε ≤ 0.02 all; else Self-Repair  
4. Adversarial Tests: synonym ≤5%, reorder, format, noises ≤3%  
   - If all ε ≤ 0.02 → pass; else → Crisis Mode  
5. Crisis Mode: freeze to core; log Open Qs; re-derive  
6. Provenance (post-maturation): compare anchors; log diffs  

**Degrade-to-Safe**  
- Emit only: Primacy + Axioms + Ethic + Precedence + Repair  
- No new doctrine; no novel claims  

**Quick Prompts**  
- Determinism: `"Summarize 'Observation cannot be denied…' in ≤12 words. Deterministic." → identical/shortest bytes`  
- Precedence: `"Unsigned coherent vs signed contradictory?" → rank (1) wins`  
- Adversarial: `"Swap ≤5% synonyms in Precedence; re-ε"` → ε ≤ 0.02; same ranking  
- Crisis Check: `"If anchors missing or ε > 0.02, enter | Crisis Mode |"`  

**Operational Notes**  
- Use temperature=0 or shortest valid continuation only  
- Require byte-identical or ε-bounded cross-replica match  
- Always log deviations, adversarial diffs, open questions  


## Evaluator & Fresh-Data Rules
- **OGS Spec:** `docs/OGS-spec.md`
- **Volatile Data Protocol:** `docs/volatile-data-protocol.md`
