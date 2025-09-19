from __future__ import annotations

from pathlib import Path

from tools.snippets import check_quickstart_docs as guard


TARGETS = [
    Path('README.md'),
    Path('docs/quickstart.md'),
]


def test_quickstart_snippet_matches_repo(tmp_path: Path):
    # Ensure canonical docs match the generated snippet.
    assert guard.run(apply=False, targets=TARGETS) == []


def test_apply_updates_mismatch(tmp_path: Path):
    sample = tmp_path / 'sample.md'
    sample.write_text("""Heading

<!-- generated: quickstart snippet -->
old snippet
""", encoding='utf-8')
    mismatches = guard.run(apply=True, targets=[sample])
    assert mismatches == [sample]
    # guard rewrites the block to the canonical snippet
    assert guard.run(apply=False, targets=[sample]) == []
