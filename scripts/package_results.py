#!/usr/bin/env python3
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from infra_lib import ROOT, scan_secrets, utc_now


def copy_if_exists(source: Path, target: Path) -> None:
    if not source.exists():
        return
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("auth.json", ".env.local"))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


if __name__ == "__main__":
    pre = scan_secrets([ROOT / "results", ROOT / "runs", ROOT / "config"])
    if pre:
        raise SystemExit(f"secret scan failed; refusing package: {pre}")
    package_id = utc_now().replace(":", "").replace("-", "")
    with tempfile.TemporaryDirectory(prefix="harness-package-") as temp:
        stage = Path(temp) / f"deepseek-v4-harness-results-{package_id}"
        for relative in ("results", "runs", "benchmarks", "graders/rubrics", "experiment.yaml",
                         "config/codex-deepseek-config.toml", "config/claude-deepseek.env.template",
                         "config/judge.yaml", "config/vision.yaml", "README_RUN_ME.md", "INFRA_NOTES.md"):
            copy_if_exists(ROOT / relative, stage / relative)
        findings = scan_secrets([stage])
        if findings:
            raise SystemExit(f"secret scan failed in staged package: {findings}")
        destination = ROOT / "packages" / stage.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        archive = shutil.make_archive(str(destination), "zip", root_dir=stage.parent, base_dir=stage.name)
    print(archive)
