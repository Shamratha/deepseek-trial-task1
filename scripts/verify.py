#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from infra_lib import CHECK_DIRS, ROOT, read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("check1", "check2", "check3"), required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    grader = ROOT / "graders" / f"{args.check}_verify.py"
    if args.check == "check3":
        grader = ROOT / "graders/check3_verify_adapter.py"
    pattern = f"{args.run_id or '*'}/*"
    failures = 0
    for run_dir in sorted((ROOT / "runs" / args.check).glob(pattern)):
        if not run_dir.is_dir():
            continue
        cmd = [sys.executable, str(grader), str(run_dir / "output")]
        if args.check != "check3":
            cmd += ["--input", str(CHECK_DIRS[args.check] / "input")]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        try:
            result = __import__("json").loads(proc.stdout)
        except Exception:
            result = {"pass": False, "score": 0, "errors": ["grader emitted invalid JSON"], "stderr": proc.stderr}
        write_json(run_dir / "verifier.json", result)
        print(f"{run_dir}: {'PASS' if result.get('pass') else 'FAIL'}")
        failures += not bool(result.get("pass"))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
