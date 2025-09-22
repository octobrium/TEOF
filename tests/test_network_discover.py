from __future__ import annotations

from pathlib import Path

from tools.network import discover


def _seed_node(tmp: Path, name: str) -> Path:
    node = tmp / name
    (node / "_report").mkdir(parents=True, exist_ok=True)
    return node


def test_discover_nodes_from_parent(tmp_path: Path) -> None:
    parent = tmp_path / "nodes"
    node_a = _seed_node(parent, "node-a")
    _seed_node(parent, "node-b")
    nodes = discover.discover_nodes([parent])
    assert {node.node_id for node in nodes} == {"node-a", "node-b"}
    assert node_a in {node.root for node in nodes}


def test_build_config(tmp_path: Path) -> None:
    node = _seed_node(tmp_path, "solo")
    config = discover.build_config([discover.NodeCandidate("solo", node)], expect=["_report/usage/*.json"])
    assert config["nodes"] == {"solo": str(node)}
    assert config["expect"] == ["_report/usage/*.json"]
