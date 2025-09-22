"""Generate Ed25519 key pairs for external adapters."""
from __future__ import annotations

import argparse
import base64
from pathlib import Path

try:
    from nacl import signing
except ImportError as exc:  # pragma: no cover - dependency guard
    raise SystemExit("PyNaCl is required; install with `pip install PyNaCl`.") from exc


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-id", required=True, help="Logical key identifier (e.g., feed.geopolitics-2025)")
    parser.add_argument(
        "--private-out",
        required=True,
        help="Path to write the private key (base64, 32 bytes)",
    )
    parser.add_argument(
        "--public-dir",
        default="governance/keys",
        help="Directory for the public key (default: governance/keys)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing key files",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    key_id = args.key_id.strip()
    if not key_id:
        raise SystemExit("key id must be non-empty")

    private_path = Path(args.private_out)
    public_dir = Path(args.public_dir)
    public_dir.mkdir(parents=True, exist_ok=True)
    public_path = public_dir / f"{key_id}.pub"

    if not args.overwrite and (private_path.exists() or public_path.exists()):
        raise SystemExit("key files already exist; use --overwrite to replace")

    signing_key = signing.SigningKey.generate()
    verify_key = signing_key.verify_key

    private_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_text(base64.b64encode(signing_key.encode()).decode("ascii") + "\n", encoding="utf-8")
    public_path.write_text(base64.b64encode(verify_key.encode()).decode("ascii") + "\n", encoding="utf-8")

    print(f"generated private key -> {private_path}")
    print(f"generated public key  -> {public_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
