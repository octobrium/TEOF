# TODO — Next Clean Release Prep

This file is a scratchpad for bundling updates into the next tagged release.  
Not maintained continuously — just a reminder for release time.

---

## Release Tasks

- [ ] **Add CHANGELOG + version tag**  
  - **Success criteria:** new tag `vX.Y.Z` exists, README + site show VDP/OGS entry.  
  - **TEOF Future:** establishes clear historical recursion points — each release is an observable node in TEOF’s evolution.  

- [ ] **Add golden test cases** (`datasets/goldens/`)  
  - **Success criteria:** running `make check` fails on illusions (e.g., missing timestamp) and passes on compliant examples.  
  - **TEOF Future:** builds the “immune system” that prevents regressions; foundation for ecosystems that cannot collapse into illusion.  

- [ ] **Wire evaluator into CI**  
  - **Success criteria:** any PR with uncited volatile data is blocked automatically.  
  - **TEOF Future:** automates self-correction; TEOF no longer relies on manual vigilance.  

- [ ] **Add Explore vs Strict mode guidance** (`README.md` / `CONTRIBUTING.md`)  
  - **Success criteria:** contributors can choose creativity vs rigor explicitly.  
  - **TEOF Future:** mirrors evolutionary process (mutation vs selection), enabling recursive acceleration.  

- [ ] **(Optional) Publish hash manifest** (`anchors/immutable.json`)  
  - **Success criteria:** repo has frozen, verifiable integrity snapshots.  
  - **TEOF Future:** enables external observers to verify alignment and persistence over time.  

---

## Roadmap Notes (Beyond Release)

### 1. Evaluator & OGS refinement
- **Success criteria:** model never gives a stale/uncited number without labeling it.  
- **TEOF Future:** locks observation as the irreducible anchor — no agent can progress without grounding.  

### 2. Personal Workflow (first TEOF use case)
- **Success criteria:** decision tree outputs are traceable (value, timestamp, source) or explicitly Uncertain, and results can be logged/tested over time.  
- **TEOF Future:** first live observer loop — your own life as the proving ground for recursive clarity.  

### 3. Feedback Loop
- **Success criteria:** evaluator → workflow → back into evaluator shows measurable improvement.  
- **TEOF Future:** demonstrates recursive self-improvement in practice, a precursor to multi-agent ecosystems.  

---

## Achievements So Far

### 1. Canonical + Core TEOF established
- **What:** Philosophy, axioms, and recursion-first alignment framework documented.  
- **TEOF Future:** Provides the unshakable foundation that all downstream ecosystems build upon.  

### 2. TAP v3.1 expanded
- **What:** Transparent Alignment Protocol integrated with explicit reference to VDP + OGS.  
- **TEOF Future:** Anchors alignment in observation, ensuring future agents cannot bypass provenance.  

### 3. Volatile Data Protocol (VDP)
- **What:** Rule requiring timestamp + source on all time-sensitive claims.  
- **TEOF Future:** Eliminates illusion-of-progress; enforces reality-grounding as a hard constraint.  

### 4. Observation Grounding Score (OGS)
- **What:** Scoring rubric + evaluator spec for volatile data integrity.  
- **TEOF Future:** Introduces machine-checkable recursion — agents can now be objectively compared and improved.  

### 5. Evaluator Tooling
- **What:** `tools/teof_evaluator.py` created to validate claims automatically.  
- **TEOF Future:** Begins the path toward automated self-correction, a key step in recursive self-improvement.  

### 6. Repo Integrity Anchoring
- **What:** Freeze-hash process confirmed for repo files.  
- **TEOF Future:** Locks in tamper-evidence and historical observability of TEOF’s evolution.  

---

## Why this matters
Together, these steps shift TEOF from **philosophy only** → **auditable, enforceable framework**.  
They’re the scaffolding required for:  
1. Reliable personal workflows (decision trees, market assessment).  
2. Scaling into multi-agent ecosystems without collapsing into illusion.  
3. Long-term persistence: TEOF as an “observer anchor” across contexts and agents.  

---

## Notes
- No need to update this file after every change.  
- At release time, use this checklist to finalize the version.  
- Once complete, this file can be deleted or archived.  
