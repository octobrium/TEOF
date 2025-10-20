from tools.maintenance import evidence_usage


def test_analyse_index_flags_orphans_and_missing_receipts():
    entries = [
        {"kind": "summary"},
        {
            "kind": "receipt",
            "path": "_report/usage/sample.json",
            "category": "usage",
            "size": 123,
            "mtime": "2025-10-19T00:00:00Z",
            "sha256": "deadbeef",
            "referenced_by": [],
        },
        {
            "kind": "receipt",
            "path": "_report/usage/active.json",
            "category": "usage",
            "size": 321,
            "mtime": "2025-10-19T01:00:00Z",
            "sha256": "beadfeed",
            "referenced_by": [{"plan_id": "P-1"}],
        },
        {
            "kind": "plan",
            "plan_id": "P-legacy",
            "path": "_plans/2025-10-19-legacy.plan.json",
            "status": "done",
            "checkpoint_status": "satisfied",
            "missing_receipts": ["_report/usage/sample.json"],
        },
    ]

    report = evidence_usage.analyse_index(entries, orphan_limit=10)

    summary = report["summary"]
    assert summary["orphan_receipts"] == 1
    assert summary["plans_missing_receipts"] == 1
    assert summary["orphan_by_category"] == {"usage": 1}

    orphan = report["orphans"][0]
    assert orphan["path"] == "_report/usage/sample.json"
    assert orphan["category"] == "usage"

    plan = report["plan_failures"][0]
    assert plan["plan_id"] == "P-legacy"
    assert plan["missing_receipts"] == ["_report/usage/sample.json"]
