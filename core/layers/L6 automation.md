# L6 — Automation

**Status:** Public minimal stance  
**Depends on:** 0, L1-L5

---

## Current Public Position

The public repo does not assume a large automation surface.

Its baseline model is:

- human-triggered use
- AI-assisted reasoning or drafting
- human verification where stakes justify it

This is deliberate. A public seed should not pretend to include a mature autonomous layer if that layer depends on private state, local tooling, or invisible supervision.

---

## Guiding Rule

Add automation only when all of the following are true:

1. the manual process is already coherent
2. the friction is recurring and measurable
3. the failure mode is inspectable
4. provenance is preserved

If automation mainly creates hidden dependency chains or decorative complexity, it is a downgrade.

---

## Safe Public Candidates

Reasonable automation around a public seed might include:

- stale-link checking
- manuscript/chapter regeneration
- pattern index building
- lightweight linting or formatting

Less reasonable for the public seed:

- private memory synthesis
- autonomous decision systems
- sensitive domain workflows with hidden context

---

## Oversight Principle

Human intervention should scale with error risk, not with ritual.

Low-stakes, reversible tasks can tolerate more automation.
High-stakes, irreversible, financial, legal, or health-relevant tasks require more direct verification.

This is not anti-automation. It is verification-weighted automation.
