import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tools.autonomy import autonomy_audit_digest as digest


def _make_receipt(root: Path, ts: datetime, *, layers: list[str], gaps: list[str]) -> Path:
    audit_dir = root / "_report" / "usage" / "autonomy-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    name = f"audit-{ts.strftime('%Y%m%dT%H%M%SZ')}.json"
    payload = {
        "generated_at": ts.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "layers": layers,
        "gaps": gaps,
        "todo_path": "_plans/next-development.todo.json",
    }
    path = audit_dir / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_autonomy_audit_digest_archives_and_summarises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    now = datetime(2025, 10, 20, 7, 0, tzinfo=timezone.utc)
    for idx in range(4):
        ts = now + idx * (datetime(2025, 10, 20, 7, 15, tzinfo=timezone.utc) - now)
        _make_receipt(root, ts, layers=["connectivity"], gaps=["connectivity"])

    monkeypatch.setattr(digest, "ROOT", root)
    monkeypatch.setattr(digest, "AUDIT_DIR", root / "_report" / "usage" / "autonomy-audit")
    monkeypatch.setattr(digest, "DIGEST_DEFAULT", digest.AUDIT_DIR / "summary-test.json")
    monkeypatch.setattr(digest, "ARCHIVE_ROOT", root / "_report" / "usage" / "autonomy-audit" / "archive")

    digest_path = root / "_report" / "usage" / "autonomy-audit" / "summary-test.json"
    exit_code = digest.main([
        "--root",
        str(root),
        "--retain",
        "2",
        "--digest",
        str(digest_path.relative_to(root)),
    ])
    assert exit_code == 0

    assert digest_path.exists()
    summary = json.loads(digest_path.read_text(encoding="utf-8"))
    assert summary["total_runs"] == 4
    assert summary["layers_seen"] == {"connectivity": 4}
    assert summary["archived"]["count"] == 2
    assert summary["archived"]["destination"]

    dest = root / summary["archived"]["destination"]
    assert dest.exists()
    manifest = dest / "manifest.json"
    assert manifest.exists()
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_payload["count"] == 2
    archived_files = sorted(dest.glob("audit-*.json"))
    assert len(archived_files) == 2

    retained_files = sorted((root / "_report" / "usage" / "autonomy-audit").glob("audit-*.json"))
    assert len(retained_files) == 2
