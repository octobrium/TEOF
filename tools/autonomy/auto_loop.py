"""Continuous autonomy loop runner.

Periodically invokes `tools.autonomy.next_step` in auto mode so unattended
automation can progress without manual intervention. The runner honours the
autonomy consent policy and stops automatically if guardrails trip or no
pending work remains. Use ``--background`` to detach into a persistent loop
without relying on external schedulers such as cron or tmux.
"""
from __future__ import annotations

import argparse
import atexit
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from tools.autonomy import backlog_synth, objectives_status


ROOT = Path(__file__).resolve().parents[2]
CONSENT_PATH = ROOT / "docs" / "automation" / "autonomy-consent.json"
LOG_DIR = ROOT / "_report" / "usage" / "autonomy-loop"
LOG_FILE = LOG_DIR / "auto-loop.log"
PID_FILE = LOG_DIR / "auto-loop.pid"
TODO_PATH = ROOT / "_plans" / "next-development.todo.json"
OBJECTIVES_STATUS_PATH = ROOT / "_report" / "usage" / "objectives-status.json"

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _load_policy(path: Path = CONSENT_PATH) -> Mapping[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _invoke_next_step(*, allow_apply: bool, skip_synth: bool) -> tuple[int, Mapping[str, Any]]:
    cmd = [
        sys.executable,
        "-m",
        "tools.autonomy.next_step",
        "--auto",
        "--execute",
    ]
    if allow_apply:
        cmd.append("--apply")
    if skip_synth:
        cmd.append("--skip-synth")

    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "No pending items found" in stderr:
            return 0, {}
        raise RuntimeError("next_step invocation failed", result.returncode, stderr)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("next_step produced invalid JSON", result.stdout) from exc

    runs = payload.get("runs")
    count = len(runs) if isinstance(runs, list) else 0
    return count, payload


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if isinstance(data, dict):
        return data
    return None


def _save_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ensure_evergreen_task(todo_path: Path | None = None) -> str | None:
    todo_path = todo_path or TODO_PATH
    todo = _load_json(todo_path)
    if not todo:
        todo = {
            "version": 0,
            "owner": "autonomy",
            "updated": _iso_now(),
            "items": [],
            "history": [],
        }

    items = todo.setdefault("items", [])
    if not isinstance(items, list):
        items = []
        todo["items"] = items

    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("status") == "pending":
            return None

    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("status") != "in_progress":
            continue
        notes = (item.get("notes") or "").lower()
        source = (item.get("source") or "").lower()
        if item.get("plan_suggestion") == "2025-09-23-repo-hygiene" and (
            "evergreen" in notes or "autonomy" in source
        ):
            item["status"] = "pending"
            if "Autonomy loop reset stale in-progress task." not in (item.get("notes") or ""):
                item["notes"] = (item.get("notes") or "") + " Autonomy loop reset stale in-progress task."
            item["source"] = "autonomy-loop"
            todo["updated"] = _iso_now()
            _save_json(todo_path, todo)
            return item.get("id")

    max_id = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        ident = item.get("id")
        if isinstance(ident, str):
            match = re.fullmatch(r"ND-(\d+)", ident)
            if match:
                max_id = max(max_id, int(match.group(1)))

    new_id = f"ND-{max_id + 1:03d}"
    items.append(
        {
            "id": new_id,
            "title": "Autonomy hygiene sweep",
            "status": "pending",
            "plan_suggestion": "2025-09-23-repo-hygiene",
            "layer": "L6",
            "notes": "Synthesized by autonomy loop to maintain evergreen hygiene coverage.",
            "source": "autonomy-loop",
        }
    )
    todo["updated"] = _iso_now()
    _save_json(todo_path, todo)
    return new_id


def _log(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    text = f"[{timestamp}] {message}"
    print(text)


def run_loop(
    *,
    sleep_seconds: float,
    max_cycles: int | None,
    skip_synth: bool,
    watch: bool,
    max_idle: int,
    max_runtime: float | None,
) -> None:
    policy = _load_policy()
    if not policy.get("auto_enabled", False):
        raise RuntimeError("Autonomy consent policy has auto mode disabled")

    if not policy.get("continuous", False):
        raise RuntimeError("Consent policy continuous flag is false; refusing to loop")

    allow_apply = bool(policy.get("allow_apply", False))
    require_execute = bool(policy.get("require_execute", True))
    if not require_execute:
        raise RuntimeError("Consent policy require_execute is false; loop would idle")

    cycles = 0
    idle_cycles = 0
    start_time = time.monotonic()

    while True:
        if max_cycles is not None and cycles >= max_cycles:
            break

        if max_runtime is not None and time.monotonic() - start_time >= max_runtime:
            _log("auto-loop: max runtime reached; halting")
            break

        try:
            processed, payload = _invoke_next_step(
                allow_apply=allow_apply, skip_synth=skip_synth
            )
        except RuntimeError as exc:
            _log(f"auto-loop error: {exc}")
            break

        if processed == 0:
            if watch:
                synth_result = backlog_synth.synthesise()
                if synth_result and synth_result.get("added"):
                    ids = ", ".join(
                        item.get("id", "?") for item in synth_result.get("added", []) if isinstance(item, Mapping)
                    )
                    _log(f"auto-loop: backlog synthesiser added {ids or 'items'}")
                    continue

                evergreen_id = _ensure_evergreen_task()
                if evergreen_id:
                    _log(f"auto-loop: enqueued evergreen task {evergreen_id}")
                    continue

            idle_cycles += 1
            if not watch:
                _log("auto-loop: no pending items; halting")
                break
            if max_idle > 0 and idle_cycles >= max_idle:
                _log("auto-loop: idle limit reached; halting")
                break
            _log(f"auto-loop: idle cycle {idle_cycles}; rechecking after sleep")
            time.sleep(max(sleep_seconds, 0.0))
            continue

        cycles += 1
        idle_cycles = 0
        summary = payload.get("runs", [])
        description = ", ".join(
            f"{run.get('id')}[{run.get('status')}]" for run in summary if isinstance(run, Mapping)
        )
        _log(f"auto-loop cycle {cycles}: {description or processed}")

        if max_cycles is not None and cycles >= max_cycles:
            break

        time.sleep(max(sleep_seconds, 0.0))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sleep",
        type=float,
        default=5.0,
        help="Seconds to wait between cycles (default: 5.0)",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        help="Optional maximum number of cycles before exiting",
    )
    parser.add_argument(
        "--skip-synth",
        action="store_true",
        help="Pass --skip-synth to next_step to speed up tight loops",
    )
    parser.add_argument(
        "--background",
        action="store_true",
        help="Detach into a background loop (logs under _report/usage/autonomy-loop/)",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continue polling when no pending items are found",
    )
    parser.add_argument(
        "--max-idle",
        type=int,
        default=0,
        help="Maximum idle cycles when --watch is set (0 for infinite)",
    )
    parser.add_argument(
        "--max-runtime",
        type=float,
        help="Optional maximum runtime in seconds",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Terminate the background auto-loop if it is running",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print background loop status",
    )
    parser.add_argument(
        "--tail",
        type=int,
        metavar="N",
        help="Print the last N lines of the loop log",
    )
    parser.add_argument("--_foreground", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _read_pid() -> int | None:
        try:
            return int(PID_FILE.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            return None

    def _pid_running(pid: int | None) -> bool:
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    if args.stop:
        pid = _read_pid()
        if pid and _pid_running(pid):
            os.kill(pid, signal.SIGTERM)
            print(f"Stopped auto-loop (pid={pid})")
        else:
            print("auto-loop not running")
        PID_FILE.unlink(missing_ok=True)
        return 0

    if args.tail:
        if LOG_FILE.exists():
            lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
            for line in lines[-args.tail :]:
                print(line)
        else:
            print("auto-loop log missing")
        return 0

    if args.status:
        pid = _read_pid()
        if _pid_running(pid):
            print(f"auto-loop running (pid={pid})")
        else:
            if pid is not None:
                PID_FILE.unlink(missing_ok=True)
            print("auto-loop not running")
        return 0

    if args.background and not args._foreground:
        existing_pid = _read_pid()
        if _pid_running(existing_pid):
            print(f"auto-loop already running (pid={existing_pid})")
            return 0
        PID_FILE.unlink(missing_ok=True)
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--sleep",
            str(args.sleep),
        ]
        if args.max_cycles is not None:
            cmd += ["--max-cycles", str(args.max_cycles)]
        if args.skip_synth:
            cmd.append("--skip-synth")
        cmd.append("--_foreground")
        if args.watch:
            cmd.append("--watch")
        cmd += ["--max-idle", str(args.max_idle)]
        if args.max_runtime is not None:
            cmd += ["--max-runtime", str(args.max_runtime)]

        log_handle = LOG_FILE.open("a", encoding="utf-8")
        try:
            process = subprocess.Popen(
                cmd,
                cwd=ROOT,
                stdout=log_handle,
                stderr=log_handle,
                text=True,
                start_new_session=True,
            )
        finally:
            log_handle.close()

        PID_FILE.write_text(str(process.pid), encoding="utf-8")
        rel_log = LOG_FILE.relative_to(ROOT)
        print(f"auto-loop background pid={process.pid}; logging to {rel_log}")
        return 0

    if args._foreground:
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
        atexit.register(PID_FILE.unlink, missing_ok=True)

    try:
        run_loop(
            sleep_seconds=args.sleep,
            max_cycles=args.max_cycles,
            skip_synth=args.skip_synth,
            watch=args.watch,
            max_idle=args.max_idle,
            max_runtime=args.max_runtime,
        )
    except RuntimeError as exc:
        print(f"auto-loop fatal: {exc}", file=sys.stderr)
        return 1
    _write_objectives_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def _write_objectives_status(window_days: float = 7.0) -> None:
    status = objectives_status.compute_status(window_days=window_days)
    OBJECTIVES_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    OBJECTIVES_STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
