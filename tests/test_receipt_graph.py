from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.observation import receipt_graph


def _setup_repo(tmp_path: Path) -> None:
    (tmp_path / "queue").mkdir()
    (tmp_path / "_plans").mkdir()
    (tmp_path / "_bus" / "claims").mkdir(parents=True, exist_ok=True)
    (tmp_path / "_report" / "usage").mkdir(parents=True, exist_ok=True)
    queue_path = tmp_path / "queue" / "053-observation-receipt-graph.md"
    queue_path.write_text("# QUEUE-053\n", encoding="utf-8")

    plan_path = tmp_path / "_plans" / "2025-11-09-observation-receipt-graph.plan.json"
    plan_payload = {
        "plan_id": "2025-11-09-observation-receipt-graph",
        "summary": "Observation graph prototype",
        "receipts": [
            "_report/agent/codex-tier2/og/tests.json",
            "_report/agent/codex-tier2/og/summary.json",
        ],
    }
    plan_path.write_text(json.dumps(plan_payload, indent=2), encoding="utf-8")

    claim_path = tmp_path / "_bus" / "claims" / "QUEUE-053.json"
    claim_path.write_text(
        json.dumps(
            {
                "task_id": "QUEUE-053",
                "agent_id": "codex-tier2",
                "plan_id": "2025-11-09-observation-receipt-graph",
                "status": "active",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_receipt_graph_builds_nodes_and_edges(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup_repo(tmp_path)
    usage_dir = tmp_path / "_report" / "usage" / "receipt-graph"

    monkeypatch.setattr(receipt_graph, "ROOT", tmp_path)
    monkeypatch.setattr(receipt_graph, "QUEUE_DIR", tmp_path / "queue")
    monkeypatch.setattr(receipt_graph, "PLANS_DIR", tmp_path / "_plans")
    monkeypatch.setattr(receipt_graph, "CLAIMS_DIR", tmp_path / "_bus" / "claims")
    monkeypatch.setattr(receipt_graph, "USAGE_DIR", usage_dir)

    mermaid_path = tmp_path / "graph.mmd"
    exit_code = receipt_graph.main(
        [
            "--task",
            "QUEUE-053",
            "--extra-receipt",
            "_report/custom/receipt.txt",
            "--mermaid",
            str(mermaid_path),
        ]
    )

    assert exit_code == 0
    generated = list(usage_dir.glob("queue-053-*.json"))
    assert generated, "graph output should exist"
    graph_data = json.loads(generated[0].read_text(encoding="utf-8"))
    node_types = {node["type"] for node in graph_data["nodes"]}
    assert {"task", "plan", "claim", "receipt"} <= node_types
    receipt_nodes = [node for node in graph_data["nodes"] if node["type"] == "receipt"]
    assert any("_report/custom/receipt.txt" in node["label"] for node in receipt_nodes)
    assert "digest" in graph_data
    assert mermaid_path.exists()
    mermaid_text = mermaid_path.read_text(encoding="utf-8")
    assert "graph TD" in mermaid_text
    assert "task_QUEUE_053" in mermaid_text


def test_receipt_graph_requires_plan(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup_repo(tmp_path)
    (tmp_path / "_bus" / "claims" / "QUEUE-053.json").write_text(
        json.dumps(
            {
                "task_id": "QUEUE-053",
                "agent_id": "codex-tier2",
                "status": "active",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(receipt_graph, "ROOT", tmp_path)
    monkeypatch.setattr(receipt_graph, "QUEUE_DIR", tmp_path / "queue")
    monkeypatch.setattr(receipt_graph, "PLANS_DIR", tmp_path / "_plans")
    monkeypatch.setattr(receipt_graph, "CLAIMS_DIR", tmp_path / "_bus" / "claims")
    monkeypatch.setattr(receipt_graph, "USAGE_DIR", tmp_path / "_report" / "usage" / "receipt-graph")

    exit_code = receipt_graph.main(["--task", "QUEUE-053", "--plan", "2025-11-09-observation-receipt-graph"])

    assert exit_code == 0


def test_receipt_graph_errors_without_queue(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _setup_repo(tmp_path)
    for path in (tmp_path / "queue").glob("*"):
        path.unlink()

    monkeypatch.setattr(receipt_graph, "ROOT", tmp_path)
    monkeypatch.setattr(receipt_graph, "QUEUE_DIR", tmp_path / "queue")
    monkeypatch.setattr(receipt_graph, "PLANS_DIR", tmp_path / "_plans")
    monkeypatch.setattr(receipt_graph, "CLAIMS_DIR", tmp_path / "_bus" / "claims")
    monkeypatch.setattr(receipt_graph, "USAGE_DIR", tmp_path / "_report" / "usage" / "receipt-graph")

    exit_code = receipt_graph.main(["--task", "QUEUE-053"])

    assert exit_code == 1
