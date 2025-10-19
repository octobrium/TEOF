import json
from pathlib import Path

from tools.impact import btc_record


def _make_ledger(tmp_path: Path) -> Path:
    ledger = {
        "version": 1,
        "wallet": "testwallet",
        "generated_at": "2025-10-07T00:00:00Z",
        "entries": [],
    }
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_btc_record_appends_entry(tmp_path: Path):
    ledger_path = _make_ledger(tmp_path)
    args = [
        "--ledger",
        str(ledger_path),
        "--txid",
        "abc",
        "--direction",
        "in",
        "--amount",
        "0.5",
        "--block-height",
        "100",
        "--observed-at",
        "2025-10-07T00:00:00Z",
        "--evidence",
        "_report/evidence.json",
        "--linked-work",
        "_plans/example.plan.json",
        "--notes",
        "Test donation",
    ]
    btc_record.main(args)

    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert len(data["entries"]) == 1
    entry = data["entries"][0]
    assert entry["amount_btc"] == "0.50000000"
    assert entry["direction"] == "in"
    assert entry["txid"] == "abc"
    assert entry["linked_work"] == ["_plans/example.plan.json"]
    assert data["receipt_sha256"]
