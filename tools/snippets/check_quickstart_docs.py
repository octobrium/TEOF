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
TARGETS = [
    ROOT / 'README.md',
    ROOT / 'docs' / 'quickstart.md',
    ROOT / 'docs' / 'AGENTS.md',
    ROOT / '.github' / 'AGENT_ONBOARDING.md',
]
MARKER = '<!-- generated: quickstart snippet -->'


def _load_snippet_lines() -> List[str]:
    payload = load_commands()
    snippet = render_markdown(payload['commands'], payload['notes'])
    return snippet.splitlines()


def _ensure_doc(doc: Path, snippet_lines: List[str], *, apply: bool) -> bool:
    text = doc.read_text(encoding='utf-8')
    lines = text.splitlines()
    try:
        start = lines.index(MARKER)
    except ValueError as exc:
        raise RuntimeError(f'marker missing in {doc}') from exc
    end = start + len(snippet_lines)
    doc_slice = lines[start:end]
    if doc_slice == snippet_lines:
        return False
    if not apply:
        return True
    lines[start:end] = snippet_lines
    doc.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return True


def run(*, apply: bool, targets: Iterable[Path]) -> List[Path]:
    snippet_lines = _load_snippet_lines()
    mismatches: List[Path] = []
    for doc in targets:
        changed = _ensure_doc(doc, snippet_lines, apply=apply)
        if changed:
            mismatches.append(doc)
    return mismatches


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Rewrite docs with the current snippet when mismatched')
    parser.add_argument('--targets', nargs='*', type=Path, default=[], help='Override target docs (defaults to canonical list)')
    args = parser.parse_args(list(argv) if argv is not None else None)
    targets = args.targets or TARGETS
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
