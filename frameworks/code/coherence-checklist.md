# TEOF Code Approach

**Version:** 0.2
**Date:** 2025-12-05
**Status:** Corrected after review

---

## Correction Notice

**v0.1 of this document attempted to reinvent code quality principles from scratch.**

This was wrong. Decades of software engineering have already produced battle-tested principles and tools. TEOF should curate and select from existing structures, not reinvent them.

---

## The Principle

**Curate, don't create.**

Reality has already tested code quality approaches through:
- Millions of developers
- Billions of lines of code
- Decades of feedback
- Continuous refinement

TEOF's role: Select which existing tools and principles align with observation primacy and persistence. Not reinvent them.

---

## Use Existing Structures

### Instead of Custom Checklist, Use:

| Need | Existing Solution |
|------|-------------------|
| Code style | Prettier, Black, gofmt |
| Static analysis | ESLint, Ruff, pylint, SonarQube |
| Complexity limits | Built into linters (cyclomatic complexity rules) |
| Dead code detection | Coverage tools, tree-shaking, linters |
| Dependency analysis | madge, deptry, import-linter |
| Testing | Jest, pytest, go test |
| CI/CD | GitHub Actions, GitLab CI |

### Instead of Custom Principles, Use:

| Need | Existing Source |
|------|-----------------|
| Code structure | Clean Code (Robert Martin) |
| Design principles | SOLID |
| System design | Unix Philosophy |
| Simplicity | YAGNI, KISS |
| Testing | TDD literature |

---

## What TEOF Adds

TEOF doesn't replace these. It provides:

1. **Selection criteria:** Which tools/principles align with persistence and coherence
2. **Integration guidance:** How tools work together
3. **Judgment framework:** When to override defaults
4. **Nothing else for code**

---

## Recommended Stack

```
Language:       Use established languages (Python, TypeScript, Go, etc.)
Linter:         Use language-standard linter with strict rules
Formatter:      Use language-standard formatter (no debates)
Tests:          Use language-standard test framework
CI:             Use existing CI (GitHub Actions, etc.)
Principles:     Clean Code + SOLID + Unix Philosophy
```

TEOF configuration = selecting which rules to enable, not writing new rules.

---

## Why v0.1 Was Wrong

The original checklist:
- Reinvented linter rules poorly
- Added TEOF jargon to existing concepts
- Created unproven criteria
- Had no community validation
- Introduced hallucination risk at every step

The parseInteger evaluation revealed: I was applying "Pattern C" rigidly without checking if it actually helped.

When challenged, I folded—but couldn't verify if the fold was correct or sycophantic.

**Conclusion:** Don't trust AI-generated principles. Use reality-tested ones.

---

## The Only Custom Element

If any TEOF-specific code guidance is needed, it's this:

**Before adding any code to TEOF systems:**
1. Can we use an existing library instead?
2. Can we use an existing pattern instead?
3. Can we use an existing tool instead?
4. Only if all three are "no" → write custom code

This is just "don't reinvent the wheel" with a checklist.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-05 | Initial draft - attempted custom checklist |
| 0.2 | 2025-12-05 | Corrected - curate existing, don't reinvent |

---

## Dialogue That Led to This Correction

See: `/memory/processed/2025-12-05-curate-dont-create.md`
