import base64
from pathlib import Path

import pytest

pytest.importorskip("nacl")

from tools.external import keys


def test_keygen_produces_files(tmp_path: Path, monkeypatch):
    private_out = tmp_path / "secret" / "feed.key"
    public_dir = tmp_path / "pub"

    argv = [
        "--key-id",
        "feed.demo-2025",
        "--private-out",
        str(private_out),
        "--public-dir",
        str(public_dir),
    ]
    keys.main(argv)

    assert private_out.exists()
    assert (public_dir / "feed.demo-2025.pub").exists()

    priv_bytes = base64.b64decode(private_out.read_text(encoding="utf-8"))
    pub_bytes = base64.b64decode((public_dir / "feed.demo-2025.pub").read_text(encoding="utf-8"))
    assert len(priv_bytes) == 32
    assert len(pub_bytes) == 32

    # Overwrite should fail without flag
    with pytest.raises(SystemExit):
        keys.main(argv)

    argv_with_overwrite = argv + ["--overwrite"]
    keys.main(argv_with_overwrite)
