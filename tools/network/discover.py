"""Discover TEOF node directories and emit a receipt-sync config stub."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class NodeCandidate:
    node_id: str
    root: Path


def _is_node(path: Path) -> bool:
    return (path / "_report").is_dir()


def discover_nodes(roots: Sequence[Path]) -> List[NodeCandidate]:
    candidates: List[NodeCandidate] = []
    for base in roots:
        if _is_node(base):
            candidates.append(NodeCandidate(node_id=base.name, root=base))
            continue
        if base.is_dir():
            for child in sorted(base.iterdir()):
                if not child.is_dir():
                    continue
                if _is_node(child):
                    candidates.append(NodeCandidate(node_id=child.name, root=child))
    return candidates


def build_config(nodes: Sequence[NodeCandidate], *, expect: Sequence[str] | None = None) -> dict:
    data = {
        "nodes": {candidate.node_id: str(candidate.root) for candidate in nodes},
    }
    if expect:
        data["expect"] = list(expect)
    return data


def _parse_roots(values: Sequence[str]) -> List[Path]:
    roots: List[Path] = []
    for value in values:
        path = Path(value)
        if not path.is_absolute():
            path = ROOT / path
        roots.append(path.resolve())
    return roots


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roots",
        nargs="+",
        help="Directories to scan for nodes (accepts node paths or parent directories)",
    )
    parser.add_argument(
        "--expect",
        action="append",
        help="Receipt glob to include in the generated config",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional output path (defaults to stdout)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    roots = _parse_roots(args.roots)
    nodes = discover_nodes(roots)
    if not nodes:
        parser.error("no nodes discovered (ensure directories contain _report/")
        return 2
    config = build_config(nodes, expect=args.expect)
    payload = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out_path = args.out if args.out.is_absolute() else (ROOT / args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        print(f"wrote {out_path}")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
