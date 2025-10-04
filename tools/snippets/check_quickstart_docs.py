#!/usr/bin/env python3
"""Ensure quickstart snippets in docs match the generated snippet."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import sys

ROOT = Path(__file__).resolve().parents[2]
if __package__:
    from .render_quickstart import load_commands, render_markdown
else:
    sys.path.append(str(Path(__file__).resolve().parent))
    from render_quickstart import load_commands, render_markdown
SNIPPET_TARGETS = [
    ROOT / 'docs' / 'quickstart.md',
]

REFERENCE_BLOCKS = {
    ROOT / 'README.md': None,
    ROOT / 'docs' / 'agents.md': None,
    ROOT / '.github' / 'AGENT_ONBOARDING.md': None,
}
MARKER = '<!-- generated: quickstart snippet -->'


def _load_snippet_lines() -> List[str]:
    payload = load_commands()
    snippet = render_markdown(payload['commands'], payload['notes'])
    return snippet.splitlines()


def _ensure_block(doc: Path, *, expected: List[str], apply: bool) -> bool:
    text = doc.read_text(encoding='utf-8')
    lines = text.splitlines()
    try:
        start = lines.index(MARKER)
    except ValueError as exc:
        raise RuntimeError(f'marker missing in {doc}') from exc
    end = start + len(expected)
    doc_slice = lines[start:end]
    if doc_slice == expected:
        return False
    if not apply:
        return True
    lines[start:end] = expected
    doc.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return True


def _ensure_snippet(doc: Path, snippet_lines: List[str], *, apply: bool) -> bool:
    return _ensure_block(doc, expected=snippet_lines, apply=apply)


def run(*, apply: bool, targets: Iterable[Path]) -> List[Path]:
    snippet_lines = _load_snippet_lines()
    mismatches: List[Path] = []
    for doc in targets:
        if doc in SNIPPET_TARGETS:
            changed = _ensure_snippet(doc, snippet_lines, apply=apply)
        else:
            try:
                expected = REFERENCE_BLOCKS[doc]
            except KeyError as exc:
                raise RuntimeError(f'no quickstart guard configuration for {doc}') from exc
            if expected is None:
                expected = snippet_lines
            changed = _ensure_block(doc, expected=expected, apply=apply)
        if changed:
            mismatches.append(doc)
    return mismatches


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Rewrite docs with the current snippet when mismatched')
    parser.add_argument('--targets', nargs='*', type=Path, default=[], help='Override target docs (defaults to canonical list)')
    args = parser.parse_args(list(argv) if argv is not None else None)
    default_targets: List[Path] = SNIPPET_TARGETS + list(REFERENCE_BLOCKS)
    targets = args.targets or default_targets
    mismatches = run(apply=args.apply, targets=targets)
    if mismatches and not args.apply:
        for doc in mismatches:
            print(f'MISMATCH: {doc}')
        return 1
    if args.apply and mismatches:
        for doc in mismatches:
            print(f'Updated {doc}')
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
