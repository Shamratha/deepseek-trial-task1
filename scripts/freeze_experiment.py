#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from infra_lib import (CHECK_DIRS, DEEPSEEK, ROOT, check3_ready, environment_snapshot,
                       hash_json, sanitized_claude_env, sanitized_codex_config,
                       parse_flat_yaml, sha256_file, tree_manifest, utc_now, write_json)


def vision_model() -> str | None:
    for line in (ROOT / "config/vision.yaml").read_text().splitlines():
        if line.strip().startswith("model:"):
            value = line.split(":", 1)[1].strip().strip("'\"")
            return None if value in ("", "null", "~") else value
    return None


def main() -> None:
    tasks = {name: (sha256_file(path / "task.md") if (path / "task.md").exists() else None)
             for name, path in CHECK_DIRS.items()}
    inputs = {name: tree_manifest(path / "input") for name, path in CHECK_DIRS.items()}
    graders = tree_manifest(ROOT / "graders")
    payload = {
        "created_utc": utc_now(), "deepseek_slug": DEEPSEEK,
        "environment": environment_snapshot(),
        "sanitized_codex_config_sha256": hashlib.sha256(sanitized_codex_config().encode()).hexdigest(),
        "sanitized_claude_environment_sha256": hash_json(sanitized_claude_env()),
        "task_sha256": tasks, "input_manifests": inputs, "vision_model": vision_model(),
        "judge_config_sha256": sha256_file(ROOT / "config/judge.yaml"),
        "timeouts": {"check1": 3600, "check2": 3600,
                     "check3": parse_flat_yaml(CHECK_DIRS["check3"] / "source.lock.yaml").get("timeout_seconds")},
        "grader_manifest": graders, "check3_team_lock_ready": check3_ready(),
        "check3_source_lock_sha256": sha256_file(CHECK_DIRS["check3"] / "source.lock.yaml"),
    }
    payload["freeze_id"] = hash_json(payload)[:16]
    history = ROOT / "results/freezes" / f"{payload['freeze_id']}.json"
    write_json(history, payload)
    write_json(ROOT / "results/frozen_manifest.json", payload)
    print(json.dumps({"freeze_id": payload["freeze_id"], "check3_ready": payload["check3_team_lock_ready"]}))


if __name__ == "__main__":
    main()
