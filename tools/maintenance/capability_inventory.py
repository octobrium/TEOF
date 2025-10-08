"""Summarise command/tool usage to highlight dormant capabilities."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from teof.commands import COMMAND_MODULES as _COMMAND_MODULES

ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = ROOT / "_report"
TESTS_ROOT = ROOT / "tests"
COMMAND_ROOT = ROOT / "teof" / "commands"

_TEXT_EXTENSIONS = {".json", ".jsonl", ".txt", ".md", ".stdout", ".log"}
COMMAND_MODULES = _COMMAND_MODULES


@dataclass
class CommandUsage:
    name: str
    module_path: Path
    tests: List[Path]
    receipt_paths: List[Path]
    last_receipt: datetime | None

    def to_payload(self, now: datetime, stale_after: timedelta | None) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "name": self.name,
            "module": str(self.module_path.relative_to(ROOT)),
            "tests": [str(path.relative_to(ROOT)) for path in self.tests],
            "test_count": len(self.tests),
        }
        if self.last_receipt is not None:
            payload["last_receipt"] = self.last_receipt.isoformat()
        if self.receipt_paths:
            payload["receipts"] = [str(path.relative_to(ROOT)) for path in self.receipt_paths]
        if stale_after is not None:
            stale = self.last_receipt is None or now - self.last_receipt > stale_after
            payload["stale"] = stale
        return payload


def _collect_tests(commands: Sequence[str]) -> Dict[str, List[Path]]:
    mapping: Dict[str, List[Path]] = {name: [] for name in commands}
    if not TESTS_ROOT.exists():
        return mapping

    for test_path in sorted(TESTS_ROOT.rglob("test_*.py")):
        try:
            text = test_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for name in commands:
            if name in text:
                mapping[name].append(test_path)
    return mapping


def _iter_receipt_matches(name: str) -> Iterable[Path]:
    if not REPORT_ROOT.exists():
        return []
    needle = f"{name}".lower()
    for path in REPORT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _TEXT_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if needle in text.lower():
            yield path


def generate_inventory(root: Path | None = None, *, stale_days: float | None = 30.0) -> List[CommandUsage]:
    del root  # legacy param for future extension
    commands = list(_COMMAND_MODULES)
    tests_mapping = _collect_tests(commands)
    now = datetime.now(timezone.utc)
    stale_after = timedelta(days=stale_days) if stale_days is not None else None

    inventory: List[CommandUsage] = []
    for name in commands:
        module_path = COMMAND_ROOT / f"{name}.py"
        receipts = list(_iter_receipt_matches(name))
        last_receipt = None
        if receipts:
            latest_path = max(receipts, key=lambda p: p.stat().st_mtime)
            last_receipt = datetime.fromtimestamp(latest_path.stat().st_mtime, timezone.utc)
        usage = CommandUsage(
            name=name,
            module_path=module_path,
            tests=tests_mapping.get(name, []),
            receipt_paths=receipts,
            last_receipt=last_receipt,
        )
        inventory.append(usage)
    return inventory


def render_table(inventory: Iterable[CommandUsage], *, stale_days: float | None) -> str:
    now = datetime.now(timezone.utc)
    stale_after = timedelta(days=stale_days) if stale_days is not None else None
    headers = ["Command", "Tests", "Last receipt", "Stale"]
    rows: List[List[str]] = []
    for usage in inventory:
        payload = usage.to_payload(now, stale_after)
        last = payload.get("last_receipt", "-")
        stale = payload.get("stale")
        rows.append([
            payload["name"],
            str(payload["test_count"]),
            last,
            "yes" if stale else "no" if stale is not None else "-",
        ])
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(str(cell)))
    fmt = " ".join(f"{{:<{w}}}" for w in widths)
    lines = [fmt.format(*headers), "-" * (sum(widths) + len(widths) - 1)]
    for row in rows:
        lines.append(fmt.format(*row))
    return "\n".join(lines)


def to_payload(inventory: Iterable[CommandUsage], *, stale_days: float | None) -> Dict[str, object]:
    now = datetime.now(timezone.utc)
    stale_after = timedelta(days=stale_days) if stale_days is not None else None
    return {
        "generated_at": now.isoformat(),
        "stale_days": stale_days,
        "commands": [usage.to_payload(now, stale_after) for usage in inventory],
    }


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("table", "json"), default="table")
    parser.add_argument("--stale-days", type=float, default=30.0, help="Mark commands without receipts newer than N days as stale (default: 30)")
    parser.add_argument("--no-stale", action="store_true", help="Disable stale calculation")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    stale_days = None if args.no_stale else args.stale_days
    inventory = generate_inventory(stale_days=stale_days)
    if args.format == "json":
        try:
            json.dump(to_payload(inventory, stale_days=stale_days), sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        except BrokenPipeError:  # pragma: no cover - streaming convenience
            return 0
        return 0
    try:
        print(render_table(inventory, stale_days=stale_days))
    except BrokenPipeError:  # pragma: no cover - streaming convenience
        return 0
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
