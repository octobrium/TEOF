from __future__ import annotations

import base64
import json
from pathlib import Path
import shutil

from nacl import signing as nacl_signing

from tools.network import receipt_sync


def _make_node(tmp: Path, node_id: str) -> Path:
    root = tmp / node_id
    (root / "_report" / "usage").mkdir(parents=True, exist_ok=True)
    (root / "governance").mkdir(parents=True, exist_ok=True)
    (root / "capsule" / "v1.0").mkdir(parents=True, exist_ok=True)
    (root / "capsule" / "v1.0" / "hashes.json").write_text(
        json.dumps({"artifact": "demo"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    current = root / "capsule" / "current"
    if current.exists() or current.is_symlink():
        current.unlink()
    try:
        current.symlink_to("v1.0")
    except OSError:
        # Fallback on systems without symlink support
        shutil.copytree((root / "capsule" / "v1.0"), current)
    (root / "governance" / "anchors.json").write_text(
        json.dumps({"anchors": []}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return root


def _write_receipt(root: Path, relative: str, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_sync_receipts_detects_conflicts(tmp_path: Path) -> None:
    node_a = _make_node(tmp_path, "node-a")
    node_b = _make_node(tmp_path, "node-b")

    rel_path = "_report/usage/external-summary.json"
    _write_receipt(
        node_a,
        rel_path,
        {
            "generated_at": "2025-09-22T18:00:00Z",
            "feeds": {"demo": {"receipt_count": 1}},
        },
    )
    _write_receipt(
        node_b,
        rel_path,
        {
            "generated_at": "2025-09-22T18:05:00Z",
            "feeds": {"demo": {"receipt_count": 2}},
        },
    )

    # Matching receipt to prove no-conflict path
    hygiene_path = "_report/usage/receipts-hygiene-summary.json"
    _write_receipt(node_a, hygiene_path, {"plans_missing_receipts": 0})
    _write_receipt(node_b, hygiene_path, {"plans_missing_receipts": 0})

    out_dir = tmp_path / "out"
    result_dir = receipt_sync.sync_receipts(
        [
            receipt_sync.NodeConfig(node_id="node-a", root=node_a),
            receipt_sync.NodeConfig(node_id="node-b", root=node_b),
        ],
        out_dir=out_dir,
        include_patterns=None,
        expected_patterns=[rel_path, hygiene_path],
        verify_anchor=True,
        verify_capsule=True,
        create_latest_symlink=False,
    )

    assert result_dir == out_dir.resolve()

    ledger = json.loads((out_dir / "ledger.json").read_text(encoding="utf-8"))
    conflicts = json.loads((out_dir / "conflicts.json").read_text(encoding="utf-8"))
    summary = (out_dir / "summary.md").read_text(encoding="utf-8")

    assert ledger["node_count"] == 2
    assert ledger["artifact_count"] >= 2
    assert any(item["path"] == rel_path for item in ledger["artifacts"])

    assert len(conflicts) == 1
    assert conflicts[0]["path"] == rel_path
    nodes = sorted({node for variant in conflicts[0]["variants"] for node in variant["nodes"]})
    assert nodes == ["node-a", "node-b"]

    # Coverage report should note that both nodes satisfied expectations
    coverage = {item["node_id"]: item for item in ledger["coverage"]}
    assert coverage["node-a"]["missing"] == []
    assert coverage["node-b"]["missing"] == []

    # Checks should pass for anchors/capsule hashes
    assert ledger["checks"]["anchor"]["status"] in {"ok", "partial"}
    assert "capsule" in ledger["checks"]

    assert "Coverage expectations" in summary
    assert "Anchor check" in summary
    assert "Conflicts detected: 1" in summary
    assert rel_path in summary


def test_cli_entrypoint(tmp_path: Path) -> None:
    node = _make_node(tmp_path, "solo")
    _write_receipt(node, "_report/usage/external-summary.json", {"ok": True})

    out_dir = tmp_path / "out-cli"
    argv = [
        "--node",
        f"solo={node}",
        "--out-dir",
        str(out_dir),
        "--expect",
        "_report/usage/external-summary.json",
        "--verify-anchor",
        "--verify-capsule",
    ]
    assert receipt_sync.main(argv) == 0
    assert (out_dir / "ledger.json").exists()


def test_signature_verification(tmp_path: Path) -> None:
    node = _make_node(tmp_path, "sig-node")
    key = nacl_signing.SigningKey.generate()
    key_id = "sig-node-1"
    key_dir = node / "governance" / "keys"
    key_dir.mkdir(parents=True, exist_ok=True)
    key_dir.joinpath(f"{key_id}.pub").write_text(
        base64.urlsafe_b64encode(key.verify_key.encode()).decode("utf-8"),
        encoding="utf-8",
    )
    body = {
        "generated_at": "2025-09-22T18:00:00Z",
        "feeds": {"demo": {"receipt_count": 1}},
    }
    canonical = json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = base64.urlsafe_b64encode(key.sign(canonical).signature).decode("utf-8")
    payload = dict(body)
    payload.update({"public_key_id": key_id, "signature": signature})
    _write_receipt(node, "_report/usage/external-summary.json", payload)

    result_dir = receipt_sync.sync_receipts(
        [receipt_sync.NodeConfig(node_id="sig-node", root=node)],
        out_dir=tmp_path / "sig-out",
        verify_signatures=True,
        create_latest_symlink=False,
    )

    ledger = json.loads((result_dir / "ledger.json").read_text(encoding="utf-8"))
    assert ledger["checks"]["signature"]["status"] == "ok"

    other_node = _make_node(tmp_path, "missing")
    _write_receipt(other_node, "_report/usage/external-summary.json", body)
    missing_dir = receipt_sync.sync_receipts(
        [receipt_sync.NodeConfig(node_id="missing", root=other_node)],
        out_dir=tmp_path / "sig-missing",
        verify_signatures=True,
        require_signatures=True,
        create_latest_symlink=False,
    )
    missing_check = json.loads((missing_dir / "ledger.json").read_text(encoding="utf-8"))["checks"]["signature"]
    assert missing_check["status"] in {"missing", "error"}


def test_config_file(tmp_path: Path) -> None:
    node_a = _make_node(tmp_path, "cfg-a")
    node_b = _make_node(tmp_path, "cfg-b")
    rel_path = "_report/usage/external-summary.json"
    _write_receipt(node_a, rel_path, {"generated_at": "2025-09-22T18:00:00Z"})
    _write_receipt(node_b, rel_path, {"generated_at": "2025-09-22T18:01:00Z"})

    config = {
        "nodes": {
            "cfg-a": str(node_a),
            "cfg-b": str(node_b),
        },
        "expect": [rel_path],
        "verify_anchor": True,
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    out_dir = tmp_path / "config-out"
    receipt_sync.main([
        "--config",
        str(config_path),
        "--out-dir",
        str(out_dir),
    ])
    assert (out_dir / "ledger.json").exists()
