#!/usr/bin/env python3
from __future__ import annotations

import argparse
from infra_lib import ARMS, run_arm, run_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("check1", "check2", "check3"), required=True)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--timeout", type=int)
    args = parser.parse_args()
    print(run_arm(args.check, args.arm, args.run_id or run_id(), args.timeout))


if __name__ == "__main__":
    main()

