"""Update docs/adoption/external-feed-registry.md with the latest feed metadata."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "docs" / "adoption" / "external-feed-registry.md"


class RegistryUpdateError(RuntimeError):
    """Raised when the registry cannot be updated."""


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Path to the registry markdown file",
    )
    parser.add_argument("--feed-id", required=True, help="Feed identifier to upsert in the registry")
    parser.add_argument(
        "--steward",
        required=True,
        help="Feed steward description (appears verbatim in the table)",
    )
    parser.add_argument(
        "--plan-path",
        required=True,
        help="Path to the governing plan JSON (relative to repo root or absolute)",
    )
    parser.add_argument(
        "--plan-id",
        help="Plan identifier to display; inferred from JSON when omitted",
    )
    parser.add_argument(
        "--key-path",
        required=True,
        help="Path to the public key file anchoring the feed",
    )
    parser.add_argument(
        "--key-id",
        help="Optional key identifier label; defaults to the filename stem",
    )
    parser.add_argument(
        "--latest-receipt",
        required=True,
        help="Path to the most recent receipt JSON emitted by the adapter",
    )
    parser.add_argument(
        "--summary-path",
        required=True,
        help="Path to the refreshed external summary JSON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the updated row without writing to disk",
    )
    return parser.parse_args(argv)


def _resolve_repo_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def _load_plan_id(plan_path: Path) -> str:
    try:
        data = json.loads(plan_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise RegistryUpdateError(f"Plan file not found: {plan_path}") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise RegistryUpdateError(f"Plan file is not valid JSON: {plan_path}") from exc
    plan_id = str(data.get("plan_id", "")).strip()
    if not plan_id:
        raise RegistryUpdateError(f"Plan file missing plan_id: {plan_path}")
    return plan_id


def _compute_label(path: Path) -> str:
    try:
        relative = path.relative_to(ROOT)
        return str(relative).replace(os.sep, "/")
    except ValueError:  # pragma: no cover - path outside repo
        return path.name


def _make_link(label: str, target: Path, registry_path: Path) -> str:
    relative = os.path.relpath(target, start=registry_path.parent)
    return f"[`{label}`]({relative.replace(os.sep, '/')})"


def _format_row(
    *,
    feed_id: str,
    steward: str,
    plan_link: str,
    key_link: str,
    receipt_link: str,
    summary_link: str,
) -> str:
    return f"| {feed_id} | {steward} | {plan_link} | {key_link} | {receipt_link} | {summary_link} |\n"


def _upsert_row(registry_path: Path, row: str, feed_id: str) -> list[str]:
    lines = registry_path.read_text(encoding="utf-8").splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"feed_id", "---"}:
            continue
        if cells[0] == feed_id:
            lines[idx] = row
            break
    else:  # feed not present, append before trailing notes bullets (first blank line after table)
        insert_idx = len(lines)
        for idx, line in enumerate(lines):
            if idx <= 1:
                continue  # skip title + blank
            if line.strip() == "" and idx > 0:
                insert_idx = idx
                break
        lines.insert(insert_idx, row)
    return lines


def update_registry(args: argparse.Namespace) -> str:
    registry_path = args.registry
    if not registry_path.is_absolute():
        registry_path = (ROOT / registry_path).resolve()
    if not registry_path.exists():
        raise RegistryUpdateError(f"Registry file not found: {registry_path}")

    plan_path = _resolve_repo_path(args.plan_path)
    key_path = _resolve_repo_path(args.key_path)
    receipt_path = _resolve_repo_path(args.latest_receipt)
    summary_path = _resolve_repo_path(args.summary_path)

    if not plan_path.exists():
        raise RegistryUpdateError(f"Plan path does not exist: {plan_path}")
    if not key_path.exists():
        raise RegistryUpdateError(f"Key path does not exist: {key_path}")
    if not receipt_path.exists():
        raise RegistryUpdateError(f"Receipt path does not exist: {receipt_path}")
    if not summary_path.exists():
        raise RegistryUpdateError(f"Summary path does not exist: {summary_path}")

    plan_id = args.plan_id or _load_plan_id(plan_path)
    key_id = args.key_id or key_path.stem

    plan_link = _make_link(plan_id, plan_path, registry_path)
    key_link = _make_link(key_id, key_path, registry_path)
    receipt_link = _make_link(_compute_label(receipt_path), receipt_path, registry_path)
    summary_link = _make_link(_compute_label(summary_path), summary_path, registry_path)

    row = _format_row(
        feed_id=args.feed_id,
        steward=args.steward,
        plan_link=plan_link,
        key_link=key_link,
        receipt_link=receipt_link,
        summary_link=summary_link,
    )

    if args.dry_run:
        return row

    lines = _upsert_row(registry_path, row, args.feed_id)
    registry_path.write_text("".join(lines), encoding="utf-8")
    return row


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
        row = update_registry(args)
    except RegistryUpdateError as exc:
        raise SystemExit(str(exc))
    if args.dry_run:
        print(row, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
