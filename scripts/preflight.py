#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

from infra_lib import (DEEPSEEK, ROOT, check3_ready, control_config_errors,
                       environment_snapshot, load_local_env, sanitized_claude_env,
                       write_json)


def help_contains(command: list[str], flag: str) -> bool:
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=20)
        return flag in (result.stdout + result.stderr)
    except Exception:
        return False


def vision_model() -> str | None:
    for line in (ROOT / "config/vision.yaml").read_text().splitlines():
        if line.strip().startswith("model:"):
            value = line.split(":", 1)[1].strip().strip("'\"")
            return None if value in ("", "null", "~") else value
    return None


def main() -> None:
    env = load_local_env()
    checks: dict[str, dict] = {}
    for command in ("codex", "claude", "git", "curl"):
        checks[f"{command}_exists"] = {"ok": shutil.which(command) is not None}
    checks["python_3_11"] = {"ok": sys.version_info >= (3, 11), "actual": sys.version.split()[0]}
    checks["codex_ephemeral"] = {"ok": help_contains(["codex", "exec", "--help"], "--ephemeral")}
    checks["codex_json"] = {"ok": help_contains(["codex", "exec", "--help"], "--json")}
    checks["claude_no_persistence"] = {"ok": help_contains(["claude", "--help"], "--no-session-persistence")}
    checks["claude_stream_json"] = {"ok": help_contains(["claude", "--help"], "stream-json")}
    config = ROOT / "state/codex-deepseek-home/config.toml"
    checks["deepseek_config"] = {"ok": config.exists() and DEEPSEEK in config.read_text()}
    pins = sanitized_claude_env()
    pin_names = ("ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
                 "ANTHROPIC_DEFAULT_OPUS_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL")
    checks["claude_model_pins"] = {"ok": all(pins.get(k) == DEEPSEEK for k in pin_names)}
    control_errors = control_config_errors(env)
    checks["control_auth"] = {"ok": not control_errors, "errors": control_errors}
    checks["openrouter_key"] = {"ok": bool(env.get("OPENROUTER_API_KEY"))}
    model = env.get("VISION_MODEL") or vision_model()
    checks["vision"] = {"ok": bool(model and env.get("VISION_OPENROUTER_API_KEY")), "model": model}
    mode = env.get("JUDGE_MODE", "athena")
    judge_ok = (mode == "athena" and all(env.get(x) for x in ("ATHENA_BASE_URL", "ATHENA_API_KEY", "ATHENA_MODEL"))) or \
               (mode == "gemini" and bool(env.get("GEMINI_API_KEY")))
    checks["judge"] = {"ok": judge_ok, "mode": mode}
    checks["check3_team_lock"] = {"ok": check3_ready()}
    if env.get("OPENROUTER_API_KEY"):
        try:
            request = urllib.request.Request("https://openrouter.ai/api/v1/models", method="GET")
            with urllib.request.urlopen(request, timeout=10) as response:
                checks["network"] = {"ok": response.status == 200}
        except Exception as exc:
            checks["network"] = {"ok": False, "error": type(exc).__name__}
    else:
        checks["network"] = {"ok": False, "skipped": "OPENROUTER_API_KEY absent"}
    snapshot = environment_snapshot()
    snapshot["preflight"] = checks
    write_json(ROOT / "results/environment.json", snapshot)
    print(json.dumps(checks, indent=2, sort_keys=True))
    required_local = [k for k in checks if k not in {"control_auth", "openrouter_key", "vision", "judge", "check3_team_lock", "network"}]
    raise SystemExit(0 if all(checks[k]["ok"] for k in required_local) else 1)


if __name__ == "__main__":
    main()

