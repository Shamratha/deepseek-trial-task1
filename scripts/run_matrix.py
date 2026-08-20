#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
from pathlib import Path

from infra_lib import ARMS, ROOT, load_local_env, run_arm, run_id


def vision_model(env):
    if env.get("VISION_MODEL"):
        return env["VISION_MODEL"]
    for line in (ROOT / "config/vision.yaml").read_text().splitlines():
        if line.strip().startswith("model:"):
            value = line.split(":", 1)[1].strip().strip("'\"")
            return None if value in ("", "null", "~") else value


def run_with_sidecar(check, arm, rid, timeout):
    if check != "check2":
        return run_arm(check, arm, rid, timeout)
    env = load_local_env()
    model = vision_model(env)
    if not env.get("VISION_OPENROUTER_API_KEY") or not model:
        raise RuntimeError("Check 2 requires VISION_MODEL and VISION_OPENROUTER_API_KEY")
    log = ROOT / "state/vision-live" / check / rid / f"{arm}.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    child = dict(os.environ)
    child.update({"VISION_MODEL": model, "VISION_OPENROUTER_API_KEY": env["VISION_OPENROUTER_API_KEY"]})
    proc = subprocess.Popen([sys.executable, str(ROOT / "tools/vision_daemon.py"), "--port", "0", "--log", str(log)],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=child)
    try:
        line = proc.stdout.readline()
        ready = json.loads(line)
        if not ready.get("ready"):
            raise RuntimeError("vision sidecar did not become ready")
        return run_arm(check, arm, rid, timeout,
                       {"VISION_DAEMON_URL": f"http://127.0.0.1:{ready['port']}"}, log)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("check1", "check2", "check3"), required=True)
    parser.add_argument("--parallel", type=int, default=3, choices=(1, 2, 3))
    parser.add_argument("--run-id")
    parser.add_argument("--timeout", type=int)
    args = parser.parse_args()
    rid = args.run_id or run_id("matrix")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = {pool.submit(run_with_sidecar, args.check, arm, rid, args.timeout): arm for arm in ARMS}
        for future in concurrent.futures.as_completed(futures):
            arm = futures[future]
            try:
                print(f"{arm}: {future.result()}")
            except Exception as exc:
                print(f"{arm}: ERROR {type(exc).__name__}: {exc}")
                raise


if __name__ == "__main__":
    main()
