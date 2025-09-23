"""Relay conductor prompts to an external API and log the responses."""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
CONDUCTOR_DIR = ROOT / "_report" / "usage" / "autonomy-conductor"
RELAY_DIR = ROOT / "_report" / "usage" / "autonomy-conductor" / "api-relay"
METABOLITE_DIR = RELAY_DIR / "metabolites"
CONSENT_PATH = ROOT / "docs" / "automation" / "autonomy-consent.json"
AUTH_PATH = ROOT / "_report" / "usage" / "external-authenticity.json"


def load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def call_openai_api(prompt: str, *, api_key: str, model: str) -> str:
    req = urllib.request.Request(
        "https://api.openai.com/v1/completions",
        data=json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "max_tokens": 256,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"API error {exc.code}: {detail}") from exc
    payload = json.loads(body)
    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError("API returned no choices")
    return choices[0].get("text", "")


def build_response_record(
    *,
    conductor_path: Path,
    prompt: str,
    raw_response: str,
    dry_run: bool,
) -> Dict[str, Any]:
    data = load_json(conductor_path)
    return {
        "conducted_at": data.get("generated_at"),
        "task": data.get("task"),
        "guardrails": data.get("guardrails"),
        "prompt": prompt,
        "api_response": raw_response,
        "dry_run": dry_run,
    }


def relay(
    *,
    api_key: str,
    model: str,
    watch: bool,
    sleep_seconds: float,
    paths: Sequence[Path] | None,
    dry_run: bool,
) -> None:
    RELAY_DIR.mkdir(parents=True, exist_ok=True)
    seen: set[Path] = set()

    if not _preflight_allows():
        print("relay: preflight failed (consent or authenticity)")
        return

    def process(path: Path) -> None:
        if path in seen:
            return
        conductor_payload = load_json(path)
        prompt = conductor_payload.get("prompt", "")
        if not prompt:
            return
        if dry_run:
            raw = "[dry-run: skip external call]"
        else:
            raw = call_openai_api(prompt, api_key=api_key, model=model)
        record = build_response_record(
            conductor_path=path, prompt=prompt, raw_response=raw, dry_run=dry_run
        )
        out_path = RELAY_DIR / f"relay-{path.stem}.json"
        out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"relay: consumed {path.relative_to(ROOT)} -> {out_path.relative_to(ROOT)}")
        seen.add(path)
        _write_metabolite(record, response_path=out_path)

    def iterate() -> None:
        if paths:
            for path in paths:
                process(path)
        else:
            for path in sorted(CONDUCTOR_DIR.glob("conductor-*.json")):
                process(path)

    try:
        iterate()
        while watch:
            time.sleep(max(sleep_seconds, 0.0))
            iterate()
    except KeyboardInterrupt:
        print("relay: halted")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY)")
    parser.add_argument("--model", default="gpt-3.5-turbo-instruct", help="Model id to call")
    parser.add_argument("--watch", action="store_true", help="Keep polling for new conductor receipts")
    parser.add_argument("--sleep", type=float, default=5.0, help="Seconds between polls when --watch is set")
    parser.add_argument("--dry-run", action="store_true", help="Skip external API call and record placeholder response")
    parser.add_argument("path", nargs="*", type=Path, help="Optional explicit conductor receipt paths")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("relay: missing API key (pass --api-key or set OPENAI_API_KEY)")
    relay(
        api_key=api_key,
        model=args.model,
        watch=args.watch,
        sleep_seconds=args.sleep,
        paths=args.path,
        dry_run=args.dry_run,
    )
    return 0


def _load_consent() -> Mapping[str, Any]:
    try:
        return json.loads(CONSENT_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _load_auth() -> Mapping[str, Any] | None:
    return load_json(AUTH_PATH)


def _preflight_allows() -> bool:
    consent = _load_consent()
    if not consent.get("auto_enabled", False):
        return False
    if consent.get("halt_on_attention_feeds", True):
        auth = _load_auth()
        if not auth:
            return False
        attention = auth.get("attention_feeds") or []
        if attention:
            return False
        overall = auth.get("overall_avg_trust")
        if not isinstance(overall, (int, float)) or overall < 0.7:
            return False
    return True


def _write_metabolite(record: Mapping[str, Any], *, response_path: Path) -> None:
    METABOLITE_DIR.mkdir(parents=True, exist_ok=True)
    task = record.get("task", {})
    meta = {
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "task_id": task.get("id"),
        "objective": "O2",
        "analysis": "API relay captured response for conductor prompt.",
        "response_record": str(response_path.relative_to(ROOT)),
    }
    out = METABOLITE_DIR / f"metabolite-{response_path.stem}.json"
    out.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
