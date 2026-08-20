#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from infra_lib import ROOT, scan_secrets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path, default=[ROOT])
    args = parser.parse_args()
    findings = scan_secrets(args.paths)
    print(json.dumps({"ok": not findings, "findings": findings}, indent=2))
    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()

