#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path

from infra_lib import CHECK_DIRS, check3_ready, parse_flat_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if not check3_ready():
        print(json.dumps({"pass": False, "blocked": True, "error": "Check 3 team lock incomplete"}))
        raise SystemExit(2)
    lock = parse_flat_yaml(CHECK_DIRS["check3"] / "source.lock.yaml")
    command = str(lock["verify_command"]).replace("{output}", str(args.output))
    proc = subprocess.run(shlex.split(command), text=True, capture_output=True, check=False)
    print(json.dumps({"pass": proc.returncode == 0, "official_score": None,
                      "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}, indent=2))
    raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()

