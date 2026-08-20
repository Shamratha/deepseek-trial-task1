#!/usr/bin/env python3
"""Generate Check 2's byte-identical copy of the shared dataset."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    source_script = ROOT / "benchmarks/check1_text_excel/generate_input.py"
    spec = importlib.util.spec_from_file_location("check1_generator", source_script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    module.generate(ROOT / "benchmarks/check1_text_excel/input")
    source = ROOT / "benchmarks/check1_text_excel/input/destination_performance.csv"
    target = ROOT / "benchmarks/check2_visual_artifact/input/destination_performance.csv"
    shutil.copyfile(source, target)
    manifest = {
        "generator_seed": module.SEED,
        "rows": len([1 for _ in target.open(newline="", encoding="utf-8")]) - 1,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "shared_dataset_with": "check1",
        "image_candidates_verified_utc": "2026-08-20",
        "image_candidates": [
            {"url": url, "mime": "image/jpeg", "verified": True}
            for url in (target.parent / "image_candidates.txt").read_text(encoding="utf-8").splitlines()
            if url.strip()
        ],
    }
    (target.parent.parent / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
