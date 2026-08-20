#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import secrets
import subprocess
import sys
from pathlib import Path

from graders.make_judge_packet import make_packet
from infra_lib import ARMS, ROOT, read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("check1", "check2", "check3"), required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    base = ROOT / "runs" / args.check
    run_ids = [base / args.run_id] if args.run_id else sorted(p for p in base.glob("*") if p.is_dir())
    rubric = ROOT / "graders/rubrics" / f"{args.check}.md"
    for run_root in run_ids:
        arms = [arm for arm in ARMS if (run_root / arm / "output").exists()]
        labels = list("ABC")[:len(arms)]
        secrets.SystemRandom().shuffle(labels)
        mapping = dict(zip(labels, arms))
        map_path = ROOT / "state/judge_maps" / args.check / f"{run_root.name}.json"
        write_json(map_path, mapping)
        for label, arm in mapping.items():
            run_dir = run_root / arm
            packet_path = ROOT / "state/judge_packets" / args.check / run_root.name / f"{label}.json"
            write_json(packet_path, make_packet(run_dir, label, rubric))
            proc = subprocess.run([sys.executable, str(ROOT / "graders/run_judge.py"), str(packet_path)],
                                  text=True, capture_output=True)
            if proc.returncode:
                raise RuntimeError(f"judge failed for {label}: {proc.stderr.strip()}")
            result = json.loads(proc.stdout)
            result["anonymous_label"] = label
            write_json(run_dir / "judge.json", result)
        print(f"judged {args.check}/{run_root.name} with blinded labels")


if __name__ == "__main__":
    main()

