## Summary
<one-sentence objective>

## Checklists

### For ALL PRs
- [ ] Objective stated in first line of description
- [ ] CI green on examples; no hidden state added
- [ ] Docs updated if behavior/commands changed

### If touching validator/evaluator logic
- [ ] Goldens updated in docs/examples/** with rationale
- [ ] Determinism triple-run passes locally
- [ ] Anchors event appended with prev_content_hash

### If promoting from experimental/ → extensions/
- [ ] Meets all criteria in docs/PROMOTION_POLICY.md
- [ ] No imports from experimental/ or archive/ in packaged modules
- [ ] Quickstart reflects the exact, tested CLI

### If freezing or de-promoting
- [ ] Moved to archive/ with “frozen as of <date/tag>”
- [ ] Docs updated to remove/redirect references
