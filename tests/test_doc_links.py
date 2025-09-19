import json

import pytest

from tools.agent import doc_links


@pytest.fixture(autouse=True)
def disable_usage_logging(monkeypatch):
    monkeypatch.setattr(doc_links, "record_usage", lambda *args, **kwargs: None)


def test_list_table_output(capsys):
    rc = doc_links.main(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Docs quick-links" in out
    assert "workflow-architecture" in out
    assert "docs/workflow.md#architecture-gate-before-writing-code" in out


def test_list_json_output(capsys):
    rc = doc_links.main(["list", "--format", "json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["version"] >= 1
    assert any(link["id"] == "consensus-ledger" for link in data["links"])


def test_show_json_output(capsys):
    rc = doc_links.main(["show", "workflow-architecture", "--format", "json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "workflow-architecture"
    assert payload["target"] == "docs/workflow.md#architecture-gate-before-writing-code"


def test_missing_manifest(monkeypatch, tmp_path):
    fake_manifest = tmp_path / "missing.json"
    monkeypatch.setattr(doc_links, "MANIFEST_PATH", fake_manifest)
    with pytest.raises(SystemExit) as excinfo:
        doc_links.main(["list"])
    assert "Manifest error" in str(excinfo.value)

def test_list_category_filter(capsys):
    rc = doc_links.main(["list", "--category", "quickstart"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "quickstart-readme" in out
    assert "quickstart-smoke" in out
    assert "workflow-architecture" not in out


def test_list_json_category(capsys):
    rc = doc_links.main(["list", "--format", "json", "--category", "quickstart"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload.get("category") == "quickstart"
    ids = [link["id"] for link in payload["links"]]
    assert "quickstart-readme" in ids
    assert all(link_id.startswith("quickstart") for link_id in ids)
