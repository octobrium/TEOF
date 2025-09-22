"""Aggregate receipts from multiple TEOF nodes and surface conflicts and checks."""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple

import base64

try:  # optional dependency for signature verification
    from nacl import exceptions as nacl_exceptions
    from nacl import signing
except ImportError:  # pragma: no cover - signature verification optional
    nacl_exceptions = None
    signing = None

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_ROOT = ROOT / "_report" / "network"


@dataclass
class NodeConfig:
    node_id: str
    root: Path


@dataclass
class ReceiptEntry:
    node_id: str
    relative_path: str
    hash_sha256: str
    size: int
    modified: str
    payload: dict


def _parse_node(value: str) -> NodeConfig:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--node expects format id=/path/to/node")
    node_id, raw_path = value.split("=", 1)
    node_id = node_id.strip()
    if not node_id:
        raise argparse.ArgumentTypeError("node id must be non-empty")
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise argparse.ArgumentTypeError(f"node path does not exist: {path}")
    return NodeConfig(node_id=node_id, root=path)


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return _hash_bytes(path.read_bytes())


def _match_patterns(rel_path: str, patterns: Sequence[str] | None) -> bool:
    if not patterns:
        return True
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


def _collect_receipts(
    config: NodeConfig,
    patterns: Sequence[str] | None,
) -> Tuple[List[ReceiptEntry], Set[str]]:
    base = config.root / "_report"
    entries: List[ReceiptEntry] = []
    seen: Set[str] = set()
    if not base.exists():
        return entries, seen
    for path in sorted(base.rglob("*.json")):
        rel = path.relative_to(config.root).as_posix()
        if not _match_patterns(rel, patterns):
            continue
        data = path.read_bytes()
        payload = json.loads(data.decode("utf-8"))  # ensure valid JSON for Observation
        entries.append(
            ReceiptEntry(
                node_id=config.node_id,
                relative_path=rel,
                hash_sha256=_hash_bytes(data),
                size=path.stat().st_size,
                modified=dt.datetime.utcfromtimestamp(path.stat().st_mtime).strftime(  # type: ignore[attr-defined]
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                payload=payload,
            )
        )
        seen.add(rel)
    return entries, seen


def _aggregate(entries: Iterable[ReceiptEntry]) -> Mapping[str, Dict[str, Dict[str, object]]]:
    artifacts: Dict[str, Dict[str, Dict[str, object]]] = {}
    for entry in entries:
        variants = artifacts.setdefault(entry.relative_path, {})
        variant = variants.setdefault(
            entry.hash_sha256,
            {
                "hash": entry.hash_sha256,
                "size": entry.size,
                "modified": entry.modified,
                "nodes": [],
            },
        )
        variant_nodes: List[str] = variant["nodes"]  # type: ignore[assignment]
        if entry.node_id not in variant_nodes:
            variant_nodes.append(entry.node_id)
    for variant_map in artifacts.values():
        for variant in variant_map.values():
            variant["nodes"] = sorted(variant["nodes"])  # type: ignore[assignment]
    return artifacts


def _build_coverage_report(
    expected_patterns: Sequence[str] | None,
    seen_map: Mapping[str, Set[str]],
) -> List[Dict[str, object]]:
    if not expected_patterns:
        return []
    report: List[Dict[str, object]] = []
    for node_id, seen in seen_map.items():
        missing = sorted(
            pattern for pattern in expected_patterns if not any(fnmatch.fnmatch(path, pattern) for path in seen)
        )
        report.append(
            {
                "node_id": node_id,
                "expected": len(expected_patterns),
                "missing": missing,
            }
        )
    return report


def _summarise_uniform(values: Mapping[str, str | None]) -> str:
    present = {v for v in values.values() if v is not None}
    missing = [node for node, value in values.items() if value is None]
    if not values:
        return "skipped"
    if len(present) <= 1:
        if missing and present:
            return "partial"
        if not present:
            return "missing"
        return "ok"
    return "conflict"


def _build_checks(
    node_configs: Sequence[NodeConfig],
    *,
    verify_anchor: bool,
    verify_capsule: bool,
    signature_results: Mapping[str, object] | None,
) -> Dict[str, object]:
    checks: Dict[str, object] = {}
    if verify_anchor:
        anchor_hashes: Dict[str, str | None] = {}
        for config in node_configs:
            anchor_hashes[config.node_id] = _hash_file(config.root / "governance" / "anchors.json")
        checks["anchor"] = {
            "status": _summarise_uniform(anchor_hashes),
            "hashes": anchor_hashes,
        }
    if verify_capsule:
        capsule_info: Dict[str, Dict[str, str | None]] = {}
        pointer_values: Dict[str, str | None] = {}
        hash_values: Dict[str, str | None] = {}
        for config in node_configs:
            current = config.root / "capsule" / "current"
            pointer: str | None = None
            hash_value: str | None = None
            if current.exists():
                if current.is_symlink():
                    try:
                        pointer = str(current.readlink())
                    except OSError:
                        pointer = str(current.resolve())
                    target_dir = current.resolve()
                elif current.is_dir():
                    pointer = current.name
                    target_dir = current
                else:
                    target_dir = current.parent
                hash_value = _hash_file(target_dir / "hashes.json")
            capsule_info[config.node_id] = {
                "pointer": pointer,
                "hash": hash_value,
            }
            pointer_values[config.node_id] = pointer
            hash_values[config.node_id] = hash_value
        checks["capsule"] = {
            "status": "conflict"
            if _summarise_uniform(pointer_values) == "conflict" or _summarise_uniform(hash_values) == "conflict"
            else _summarise_uniform(hash_values if hash_values else pointer_values),
            "values": capsule_info,
        }
    if signature_results is not None:
        checks["signature"] = signature_results
    return checks


def _build_ledger(
    node_configs: Sequence[NodeConfig],
    artifacts: Mapping[str, Dict[str, Dict[str, object]]],
    timestamp: str,
    coverage: Sequence[Mapping[str, object]],
    checks: Mapping[str, object],
) -> Dict[str, object]:
    return {
        "generated_at": timestamp,
        "node_count": len(node_configs),
        "nodes": [
            {
                "node_id": config.node_id,
                "root": str(config.root),
            }
            for config in node_configs
        ],
        "artifact_count": len(artifacts),
        "artifacts": [
            {
                "path": path,
                "variants": [variant for variant in sorted(variant_map.values(), key=lambda v: v["hash"])],
            }
            for path, variant_map in sorted(artifacts.items())
        ],
        "coverage": list(coverage),
        "checks": dict(checks),
    }


def _extract_conflicts(
    artifacts: Mapping[str, Dict[str, Dict[str, object]]]
) -> List[Dict[str, object]]:
    conflicts: List[Dict[str, object]] = []
    for path, variant_map in sorted(artifacts.items()):
        if len(variant_map) <= 1:
            continue
        conflicts.append(
            {
                "path": path,
                "variant_count": len(variant_map),
                "variants": [variant for variant in sorted(variant_map.values(), key=lambda v: v["hash"])],
            }
        )
    return conflicts


def _write_outputs(
    out_dir: Path,
    ledger: Mapping[str, object],
    conflicts: Sequence[Mapping[str, object]],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "conflicts.json").write_text(json.dumps(conflicts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_lines = [
        "# Receipt sync summary\n",
        f"Generated at: {ledger['generated_at']}\n",
        f"Nodes: {ledger['node_count']}\n",
        f"Artifacts scanned: {ledger['artifact_count']}\n",
    ]
    if ledger.get("coverage"):
        summary_lines.append(f"Coverage expectations: {len(ledger['coverage'])} node(s) checked\n")
        for item in ledger["coverage"]:
            missing = item.get("missing", [])
            if missing:
                summary_lines.append(
                    f"- {item['node_id']}: missing {', '.join(missing)}\n"
                )
    checks = ledger.get("checks", {})
    if checks:
        for name, payload in checks.items():
            summary_lines.append(f"{name.capitalize()} check: {payload.get('status', 'skipped')}\n")
    if conflicts:
        summary_lines.append(f"Conflicts detected: {len(conflicts)}\n")
        for conflict in conflicts[:10]:
            join_nodes = ["/".join(variant.get("nodes", [])) for variant in conflict["variants"]]
            summary_lines.append(
                f"- {conflict['path']} → {conflict['variant_count']} variants ({', '.join(join_nodes)})\n"
            )
    else:
        summary_lines.append("Conflicts detected: 0\n")
    (out_dir / "summary.md").write_text("".join(summary_lines), encoding="utf-8")


def _load_verify_key(base: Path, key_id: str) -> signing.VerifyKey | None:
    if signing is None:
        return None
    key_path = base / "governance" / "keys" / f"{key_id}.pub"
    if not key_path.exists():
        return None
    raw = key_path.read_text(encoding="utf-8").strip()
    try:
        key_bytes = base64.urlsafe_b64decode(raw)
    except Exception:  # pragma: no cover - defensive
        return None
    if len(key_bytes) != 32:
        return None
    try:
        return signing.VerifyKey(key_bytes)
    except Exception:  # pragma: no cover - defensive
        return None


def _verify_signatures(
    entries: Sequence[ReceiptEntry],
    node_map: Mapping[str, NodeConfig],
    *,
    verify_signature: bool,
    require_signature: bool,
) -> Mapping[str, object]:
    if not verify_signature and not require_signature:
        return {"status": "skipped"}
    results: List[Dict[str, object]] = []
    overall_status = "ok"
    for entry in entries:
        payload = entry.payload
        signature = payload.get("signature")
        key_id = payload.get("public_key_id")
        status = "ok"
        reason = None
        if not signature or not key_id:
            if require_signature:
                status = "missing"
                reason = "signature_required"
                overall_status = "missing"
            else:
                status = "skipped"
            results.append(
                {
                    "path": entry.relative_path,
                    "node": entry.node_id,
                    "status": status,
                    "reason": reason,
                }
            )
            continue
        if signing is None:
            if verify_signature:
                status = "unavailable"
                reason = "pynacl_missing"
                overall_status = "error"
            results.append(
                {
                    "path": entry.relative_path,
                    "node": entry.node_id,
                    "status": status,
                    "reason": reason,
                }
            )
            continue
        node_config = node_map.get(entry.node_id)
        verify_key = _load_verify_key(node_config.root if node_config else ROOT, str(key_id)) if node_config else None
        if verify_key is None:
            status = "unknown_key"
            reason = str(key_id)
            overall_status = "error"
        else:
            try:
                sig_bytes = base64.urlsafe_b64decode(signature)
                body = {
                    k: payload[k]
                    for k in payload
                    if k not in {"signature", "public_key_id"}
                }
                verify_key.verify(
                    json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"),
                    sig_bytes,
                )
            except Exception as exc:  # pragma: no cover - narrow below
                status = "invalid"
                reason = str(exc)
                overall_status = "error"
        results.append(
            {
                "path": entry.relative_path,
                "node": entry.node_id,
                "status": status,
                "key_id": key_id,
                "reason": reason,
            }
        )
    return {
        "status": overall_status,
        "results": results,
    }


def sync_receipts(
    node_configs: Sequence[NodeConfig],
    *,
    out_root: Path = DEFAULT_OUT_ROOT,
    out_dir: Path | None = None,
    include_patterns: Sequence[str] | None = None,
    expected_patterns: Sequence[str] | None = None,
    verify_anchor: bool = False,
    verify_capsule: bool = False,
    verify_signatures: bool = False,
    require_signatures: bool = False,
    create_latest_symlink: bool = True,
) -> Path:
    if not node_configs:
        raise ValueError("at least one node must be provided")
    timestamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    target = out_dir.resolve() if out_dir is not None else (out_root / timestamp)
    entries: List[ReceiptEntry] = []
    seen_map: Dict[str, Set[str]] = {}
    for config in node_configs:
        node_entries, seen = _collect_receipts(config, include_patterns)
        entries.extend(node_entries)
        seen_map[config.node_id] = seen
    artifacts = _aggregate(entries)
    coverage = _build_coverage_report(expected_patterns, seen_map)
    node_map = {config.node_id: config for config in node_configs}
    signature_results = _verify_signatures(
        entries,
        node_map,
        verify_signature=verify_signatures,
        require_signature=require_signatures,
    )
    checks = _build_checks(
        node_configs,
        verify_anchor=verify_anchor,
        verify_capsule=verify_capsule,
        signature_results=signature_results,
    )
    ledger = _build_ledger(node_configs, artifacts, timestamp, coverage, checks)
    conflicts = _extract_conflicts(artifacts)
    _write_outputs(target, ledger, conflicts)
    if create_latest_symlink and out_dir is None:
        latest = out_root / "latest"
        latest.parent.mkdir(parents=True, exist_ok=True)
        if latest.exists() or latest.is_symlink():
            if latest.is_symlink() or latest.is_file():
                latest.unlink()
            else:
                shutil.rmtree(latest)
        try:
            latest.symlink_to(target, target_is_directory=True)
        except OSError:
            if latest.exists():
                if latest.is_symlink() or latest.is_file():
                    latest.unlink()
                elif latest.is_dir():
                    shutil.rmtree(latest)
            shutil.copytree(target, latest)
    return target


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--node",
        dest="nodes",
        action="append",
        help="Register a node mapping in the form id=/absolute/path/to/node",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional JSON config with nodes + options",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=DEFAULT_OUT_ROOT,
        help="Root directory for aggregated outputs (default: _report/network)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Optional explicit output directory; disables latest symlink when set",
    )
    parser.add_argument(
        "--include",
        action="append",
        help="Glob pattern(s) relative to each node root for receipts to include",
    )
    parser.add_argument(
        "--expect",
        action="append",
        help="Glob pattern(s) expected from every node (used for coverage reporting)",
    )
    parser.add_argument(
        "--verify-anchor",
        action="store_true",
        help="Verify governance/anchors.json hashes are identical across nodes",
    )
    parser.add_argument(
        "--verify-capsule",
        action="store_true",
        help="Verify capsule/current hashes.json contents match across nodes",
    )
    parser.add_argument(
        "--verify-signatures",
        action="store_true",
        help="Validate receipt signatures when present",
    )
    parser.add_argument(
        "--require-signatures",
        action="store_true",
        help="Fail checks when receipts lack signature metadata",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        config_data: Dict[str, object] = {}
        if args.config is not None:
            config_path = args.config if args.config.is_absolute() else (ROOT / args.config)
            try:
                config_data = json.loads(config_path.read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                raise ValueError(f"config not found: {config_path}") from exc
            except json.JSONDecodeError as exc:
                raise ValueError(f"config is not valid JSON: {config_path}") from exc

        config_nodes = config_data.get("nodes", {}) if isinstance(config_data, dict) else {}
        config_node_items: List[NodeConfig] = []
        if isinstance(config_nodes, dict):
            for node_id, path in config_nodes.items():
                if not isinstance(node_id, str) or not isinstance(path, str):
                    raise ValueError("config nodes must map id -> path strings")
                config_node_items.append(_parse_node(f"{node_id}={path}"))

        cli_nodes = args.nodes or []
        node_configs = config_node_items + [_parse_node(value) for value in cli_nodes]
        if not node_configs:
            raise ValueError("no nodes provided (use --config or --node)")

        out_root = args.out_root if args.out_root.is_absolute() else (ROOT / args.out_root)
        out_dir = None
        if args.out_dir is not None:
            out_dir = args.out_dir if args.out_dir.is_absolute() else (ROOT / args.out_dir)
        include = args.include or config_data.get("include") if isinstance(config_data, dict) else args.include
        expect = args.expect or config_data.get("expect") if isinstance(config_data, dict) else args.expect
        if include is not None and not isinstance(include, list):
            include = [include]
        if expect is not None and not isinstance(expect, list):
            expect = [expect]
        verify_anchor = args.verify_anchor or bool(config_data.get("verify_anchor")) if isinstance(config_data, dict) else args.verify_anchor
        verify_capsule = args.verify_capsule or bool(config_data.get("verify_capsule")) if isinstance(config_data, dict) else args.verify_capsule
        verify_signatures_flag = args.verify_signatures if hasattr(args, "verify_signatures") else False
        require_signatures_flag = args.require_signatures if hasattr(args, "require_signatures") else False
        if isinstance(config_data, dict):
            verify_signatures_flag = verify_signatures_flag or bool(config_data.get("verify_signatures"))
            require_signatures_flag = require_signatures_flag or bool(config_data.get("require_signatures"))
        sync_receipts(
            node_configs,
            out_root=out_root,
            out_dir=out_dir,
            include_patterns=include,
            expected_patterns=expect,
            verify_anchor=verify_anchor,
            verify_capsule=verify_capsule,
            verify_signatures=verify_signatures_flag or require_signatures_flag,
            require_signatures=require_signatures_flag,
            create_latest_symlink=args.out_dir is None,
        )
    except Exception as exc:  # pragma: no cover - CLI guard rail
        parser.error(str(exc))
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
