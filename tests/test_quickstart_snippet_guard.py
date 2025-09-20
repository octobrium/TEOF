from __future__ import annotations

from pathlib import Path

from tools.snippets import check_quickstart_docs as guard


TARGETS = guard.SNIPPET_TARGETS + list(guard.REFERENCE_BLOCKS)


def test_quickstart_snippet_matches_repo(tmp_path: Path):
    # Ensure canonical docs match the generated snippet.
    assert guard.run(apply=False, targets=TARGETS) == []


def test_apply_updates_mismatch(tmp_path: Path):
    snippet_doc = tmp_path / 'quickstart.md'
    snippet_doc.write_text("""Header

<!-- generated: quickstart snippet -->
old snippet
""", encoding='utf-8')
    reference_doc = tmp_path / 'README.md'
    reference_doc.write_text("""Heading

<!-- generated: quickstart snippet -->
old reference
""", encoding='utf-8')

    original_snippet_targets = guard.SNIPPET_TARGETS.copy()
    original_reference_blocks = guard.REFERENCE_BLOCKS.copy()
    guard.SNIPPET_TARGETS = [snippet_doc]
    guard.REFERENCE_BLOCKS = {
        reference_doc: [
            '<!-- generated: quickstart snippet -->',
            'expected reference',
            '',
        ],
    }
    try:
        targets = [snippet_doc, reference_doc]
        mismatches = guard.run(apply=True, targets=targets)
        assert mismatches == targets

        # guard rewrites both blocks to the canonical forms
        assert guard.run(apply=False, targets=targets) == []
    finally:
        guard.SNIPPET_TARGETS = original_snippet_targets
        guard.REFERENCE_BLOCKS = original_reference_blocks
