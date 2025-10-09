"""Summarise automation modules for test and receipt coverage."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterator, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTONOMY_ROOT = REPO_ROOT / "tools" / "autonomy"
REPORT_ROOT = REPO_ROOT / "_report"
TESTS_ROOT = REPO_ROOT / "tests"
_TEXT_EXTENSIONS = {".json", ".jsonl", ".txt", ".md"}


@dataclass
class AutomationEntry:
    module: str
    path: Path
    tests: List[Path]
    receipts: List[Path]
    last_receipt: datetime | None

    def is_stale(self, threshold: timedelta | None) -> bool:
        if threshold is None:
            return False
        if self.last_receipt is None:
            return True
        return datetime.now(timezone.utc) - self.last_receipt > threshold


def _iter_autonomy_modules() -> Iterator[AutomationEntry]:
    for path in sorted(AUTONOMY_ROOT.glob("*.py")):
        if path.name in {"shared.py", "__init__.py"}:
            continue
        module_name = f"tools.autonomy.{path.stem}"
        yield AutomationEntry(
            module=module_name,
            path=path,
            tests=[],
            receipts=[],
            last_receipt=None,
        )


def _collect_tests(entry: AutomationEntry) -> None:
    if not TESTS_ROOT.exists():
        return
    hits: List[Path] = []
    for test_path in TESTS_ROOT.rglob("test_*.py"):
        try:
            text = test_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None

        found = False
        if tree is not None:
            stem = entry.path.stem
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == entry.module:
                            found = True
                            break
                        if alias.name == f"tools.autonomy.{stem}":
                            found = True
                            break
                elif isinstance(node, ast.ImportFrom):
                    if node.module == "tools.autonomy" and any(
                        alias.name == stem for alias in node.names
                    ):
                        found = True
                        break
                    if node.module == entry.module or node.module == f"tools.autonomy.{stem}":
                        found = True
                        break
                if found:
                    break
        if not found:
            token = entry.module.replace(".", "_")
            if (
                entry.module in text
                or token in text
                or entry.path.stem in text
            ):
                found = True
        if found:
            hits.append(test_path)
    entry.tests = hits


def _collect_receipts(entry: AutomationEntry) -> None:
    if not REPORT_ROOT.exists():
        return
    token = entry.module.split(".")[-1]
    hits: List[Path] = []
    latest: datetime | None = None
    for path in REPORT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _TEXT_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if token not in text and entry.path.stem not in text:
            continue
        hits.append(path)
        ts = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if latest is None or ts > latest:
            latest = ts
    entry.receipts = sorted(hits)
    entry.last_receipt = latest


def generate_inventory(*, stale_days: float | None = 30.0) -> List[AutomationEntry]:
    entries = list(_iter_autonomy_modules())
    for entry in entries:
        _collect_tests(entry)
        _collect_receipts(entry)
    return entries


def _stale_threshold(stale_days: float | None) -> timedelta | None:
    return None if stale_days is None else timedelta(days=stale_days)


def to_payload(entries: Sequence[AutomationEntry], *, stale_days: float | None) -> Dict[str, object]:
    threshold = _stale_threshold(stale_days)
    now = datetime.now(timezone.utc)
    return {
        "generated_at": now.isoformat(),
        "stale_days": stale_days,
        "modules": [
            {
                "module": entry.module,
                "path": str(entry.path.relative_to(REPO_ROOT)),
                "test_count": len(entry.tests),
                "tests": [str(path.relative_to(REPO_ROOT)) for path in entry.tests],
                "receipt_count": len(entry.receipts),
                "last_receipt": entry.last_receipt.isoformat() if entry.last_receipt else None,
                "stale": entry.is_stale(threshold),
            }
            for entry in entries
        ],
    }


def render_table(entries: Sequence[AutomationEntry], *, stale_days: float | None) -> str:
    threshold = _stale_threshold(stale_days)
    headers = ["Module", "Tests", "Receipts", "Last Receipt", "Stale"]
    rows: List[List[str]] = []
    for entry in entries:
        last = entry.last_receipt.isoformat() if entry.last_receipt else "-"
        stale = "yes" if entry.is_stale(threshold) else "no"
        rows.append(
            [entry.module, str(len(entry.tests)), str(len(entry.receipts)), last, stale]
        )
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    fmt = " ".join(f"{{:<{w}}}" for w in widths)
    lines = [fmt.format(*headers), "-" * (sum(widths) + len(widths) - 1)]
    for row in rows:
        lines.append(fmt.format(*row))
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("table", "json"), default="table")
    parser.add_argument("--stale-days", type=float, default=30.0)
    parser.add_argument("--no-stale", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    stale_days = None if args.no_stale else args.stale_days
    entries = generate_inventory(stale_days=stale_days)

    if args.format == "json":
        json.dump(to_payload(entries, stale_days=stale_days), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    print(render_table(entries, stale_days=stale_days))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
