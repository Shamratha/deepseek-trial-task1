#!/usr/bin/env python3
from __future__ import annotations

import argparse
from infra_lib import ARMS, prepare_workspace, run_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("check1", "check2", "check3"), required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    rid = args.run_id or run_id("prepared")
    for arm in ARMS:
        print(prepare_workspace(args.check, rid, arm))


if __name__ == "__main__":
    main()

