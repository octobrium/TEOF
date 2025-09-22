import json
from importlib import reload
from pathlib import Path

import scripts.ci.check_vdp as check_vdp


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _prepare_module(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "datasets" / "goldens"
    docs_dir = tmp_path / "docs"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    check_vdp.ROOT = tmp_path
    check_vdp.DATASET_DIR = dataset_dir
    check_vdp.TARGET_DIRS = [docs_dir, tmp_path / "datasets"]
    reload(check_vdp)
    check_vdp.ROOT = tmp_path
    check_vdp.DATASET_DIR = dataset_dir
    check_vdp.TARGET_DIRS = [docs_dir, tmp_path / "datasets"]


def test_check_vdp_main_success(tmp_path):
    _prepare_module(tmp_path)
    pass_payload = {
        "ocers": {"result": "pass"},
        "observations": [
            {
                "label": "BTC",
                "value": 1,
                "timestamp_utc": "2099-01-01T00:00:00Z",
                "source": "https://ex/pass",
                "volatile": True,
                "stale_labeled": False,
            }
        ],
    }
    fail_payload = {
        "ocers": {"result": "fail"},
        "observations": [
            {
                "label": "NVDA",
                "value": 2,
                "source": "https://ex/fail",
                "volatile": True,
            }
        ],
    }
    _write_json(tmp_path / "datasets" / "goldens" / "pass.json", pass_payload)
    _write_json(tmp_path / "datasets" / "goldens" / "fail.json", fail_payload)

    # Repo payload referencing observations should also pass.
    _write_json(tmp_path / "docs" / "ok.json", pass_payload)

    rc = check_vdp.main()
    assert rc == 0


def test_check_vdp_flags_repo_violations(tmp_path):
    _prepare_module(tmp_path)
    pass_payload = {
        "ocers": {"result": "pass"},
        "observations": [
            {
                "label": "BTC",
                "value": 1,
                "timestamp_utc": "2099-01-01T00:00:00Z",
                "source": "https://ex/pass",
                "volatile": True,
                "stale_labeled": False,
            }
        ],
    }
    _write_json(tmp_path / "datasets" / "goldens" / "pass.json", pass_payload)

    bad_payload = {
        "observations": [
            {
                "label": "Bad",
                "value": 10,
                "volatile": True,
                "stale_labeled": False,
            }
        ],
    }
    _write_json(tmp_path / "docs" / "bad.json", bad_payload)

    rc = check_vdp.main()
    assert rc == 1
