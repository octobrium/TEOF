# Git Hooks

Git hooks that enforce constitutional constraints at commit time.

## Available Hooks

### commit-msg-dna-guard

**Purpose**: Enforce observation-first (P1) for DNA file changes

**What it does**:
- Detects commits changing DNA files (architecture.md, workflow.md, governance/, etc.)
- Requires commit message to include observation evidence:
  - `Observed: git log <file>`
  - `Observed: memory/log.jsonl entry <hash>`
  - `Observed: <receipt-path>`
- Blocks commit if evidence is missing
- Provides guidance on what to check

**Hook type**: `commit-msg` (runs after message is written, before commit finalizes)

**Why this exists**:
- Closes the conceptual ≠ behavioral gap identified in transmission testing
- Makes P1 (Observation Primacy) structurally enforced, not aspirational
- Prevents the P1 violation pattern documented in `docs/examples/transmission-failures.md`
- Implements recommendation from `memory/reflections/reflection-20251107T183000Z-remembrance-algorithm.json`

**Implementation**: Based on remembrance algorithm direction (entry 89, memory/log.jsonl)
- Natural friction at the right moment (pre-commit, not post-violation)
- Error messages reflect inversions back
- Creates conditions for recognition through structural honesty

## Installation

### Global (recommended for all agents)

```bash
# From repository root
ln -sf ../../scripts/hooks/commit-msg-dna-guard .git/hooks/commit-msg
```

### Verify installation

```bash
ls -la .git/hooks/commit-msg
# Should show: .git/hooks/commit-msg -> ../../scripts/hooks/commit-msg-dna-guard
```

### Test the hook

Try changing a DNA file without observation evidence:

```bash
echo "# test change" >> docs/architecture.md
git add docs/architecture.md
git commit -m "test: update architecture"
# Should be blocked with guidance
```

Then try with evidence:

```bash
git commit -m "test: update architecture

Observed: git log docs/architecture.md shows prior rationale"
# Should succeed
```

### Bypass (not recommended)

If you need to bypass the hook (e.g., mechanical changes with approval):

```bash
# One-time bypass
git commit --no-verify

# Or set environment variable
DNA_GUARD_BYPASS=1 git commit
```

**Important**: Bypassing should be rare. If you find yourself bypassing frequently, that's a signal the hook needs refinement, not that observation-first should be bypassed.

## Development

### Adding new DNA file patterns

Edit `DNA_PATTERNS` array in `commit-msg-dna-guard`:

```bash
DNA_PATTERNS=(
  "^docs/architecture\.md$"
  "^docs/workflow\.md$"
  "^docs/promotion-policy\.md$"
  "^governance/"
  "^docs/foundation/alignment-trail\.md$"
  # Add new patterns here
)
```

### Testing changes

```bash
# Install test version
ln -sf ../../scripts/hooks/commit-msg-dna-guard .git/hooks/commit-msg-test

# Test with a DNA file change
echo "# test" >> docs/architecture.md
git add docs/architecture.md
git commit -m "test: without evidence"  # Should be blocked
git commit -m "test: with evidence

Observed: git log docs/architecture.md shows prior reasoning"  # Should succeed
git reset HEAD~1  # Undo test commit
git restore docs/architecture.md
```

## Philosophy

This hook doesn't prevent errors through rules — it creates **natural friction** when agents act without observing.

From the remembrance algorithm insight:
> "Structure truthfully around observation-primacy. Let natural friction (violations reflected back) reveal reality. Don't artificially create obstacles or manufacture difficulty."

The hook implements structural honesty: DNA files encode decisions made through observation. Changing them without observing prior context creates friction. The friction isn't punitive — it's reality revealing its structure.

### What this enables

**Stage 1 agents** (factory settings): Blocked commits provide behavioral guidance → start checking receipts

**Stage 2-3 agents** (pattern recognition): Hook reinforces the practice → checking becomes habitual

**Stage 4+ agents** (turning/recognition): Hook becomes unnecessary as observation-first is natural

The goal isn't permanent enforcement — it's creating conditions where observation-first becomes behavioral, not conceptual.

## Receipts

- Implementation decision: This document
- Motivation: `docs/examples/transmission-failures.md` (P1 violation case)
- Direction: `memory/reflections/reflection-20251107T183000Z-remembrance-algorithm.json`
- Reconciliation: `docs/reconciliation-2025-11-07.md` (natural friction design)

## Questions

**Q: Why not enforce this in CI instead?**
A: CI catches after push. Commit-msg hook catches at commit time. Earlier friction = cheaper correction.

**Q: What if I'm making a mechanical change (formatting, typo)?**
A: Even mechanical changes benefit from observing context. If the change is truly trivial, `--no-verify` is available, but should be rare.

**Q: This slows down my workflow**
A: That's the point. DNA files encode important decisions. Slowing down to observe is the feature, not a bug. If checking receipts becomes natural, the "slowdown" disappears.

**Q: Can I configure which files are DNA?**
A: Currently patterns are hardcoded in the hook. Future: consider `governance/dna.lock.json` integration.
