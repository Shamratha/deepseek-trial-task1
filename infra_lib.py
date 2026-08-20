"""Shared, stdlib-only experiment orchestration primitives."""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import os
import platform
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent
DEEPSEEK = "deepseek/deepseek-v4-flash-0731"
ARMS = ("control_native_codex", "exp_codexcli_deepseek", "exp_claudecode_deepseek")
CHECK_DIRS = {
    "check1": ROOT / "benchmarks/check1_text_excel",
    "check2": ROOT / "benchmarks/check2_visual_artifact",
    "check2_hard": ROOT / "benchmarks/check2_hard",
    "check3": ROOT / "benchmarks/check3_e2e",
}
SECRET_NAME_RE = re.compile(r"(key|token|secret|password|auth)", re.I)
SECRET_VALUE_RE = re.compile(
    r"(?i)(sk-or-v1-[A-Za-z0-9_-]{12,}|(?:bearer\s+)[A-Za-z0-9._~+/-]{12,}|"
    r"(?:access|refresh)[_-]?token\s*[:=]\s*['\"]?[A-Za-z0-9._~+/-]{12,})"
)
METRIC_FIELDS = [
    "check_id", "run_id", "arm", "harness", "configured_model", "actual_model",
    "provider", "status", "exit_code", "timed_out", "wall_seconds", "input_tokens",
    "cached_input_tokens", "cache_creation_input_tokens", "output_tokens",
    "reasoning_output_tokens", "total_tokens", "main_model_reported_cost_usd",
    "vision_calls", "vision_input_tokens", "vision_output_tokens",
    "vision_reported_cost_usd", "combined_reported_cost_usd", "deterministic_score",
    "official_verifier_pass", "official_verifier_score", "judge_score",
    "human_interventions", "files_created", "notes",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    files = []
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        files.append({"path": item.relative_to(path).as_posix(), "bytes": item.stat().st_size,
                      "sha256": sha256_file(item)})
    return files


def hash_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_local_env() -> dict[str, str]:
    values = dict(os.environ)
    path = ROOT / "config/.env.local"
    if not path.exists():
        return values
    if path.stat().st_mode & 0o077:
        raise RuntimeError("config/.env.local must have mode 0600")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def parse_flat_yaml(path: Path) -> dict[str, Any]:
    """Read the intentionally flat Check 3 lock without executing YAML tags."""
    result: dict[str, Any] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value in ("null", "~", ""):
            parsed: Any = None
        elif value.lower() in ("true", "false"):
            parsed = value.lower() == "true"
        elif re.fullmatch(r"[0-9]+", value):
            parsed = int(value)
        else:
            parsed = value.strip("'\"")
        result[key.strip()] = parsed
    return result


def check3_ready() -> bool:
    lock = parse_flat_yaml(CHECK_DIRS["check3"] / "source.lock.yaml")
    required = ("field", "owner", "repo", "ref", "seed", "run_command", "verify_command", "timeout_seconds")
    return lock.get("ready") is True and all(lock.get(k) for k in required)


def sanitized_codex_config() -> str:
    text = (ROOT / "config/codex-deepseek-config.toml").read_text(encoding="utf-8")
    return SECRET_VALUE_RE.sub("<REDACTED>", text)


def sanitized_claude_env() -> dict[str, str]:
    result = {}
    for line in (ROOT / "config/claude-deepseek.env.template").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key] = "<FROM_ENV>" if SECRET_NAME_RE.search(key) else value
    return result


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: ("<REDACTED>" if SECRET_NAME_RE.search(k) else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return SECRET_VALUE_RE.sub("<REDACTED>", value)
    return value


def command_output(args: list[str]) -> str | None:
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=20, check=False)
        value = (proc.stdout or proc.stderr).strip()
        return value.splitlines()[0] if value else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def environment_snapshot() -> dict[str, Any]:
    return {
        "captured_utc": utc_now(), "codex": command_output(["codex", "--version"]),
        "claude": command_output(["claude", "--version"]),
        "python": platform.python_version(), "python_executable": sys.executable,
        "git": command_output(["git", "--version"]), "uname": " ".join(platform.uname()),
        "macos": platform.mac_ver()[0] or None,
    }


def control_config_errors(env: dict[str, str]) -> list[str]:
    errors = []
    home_raw = env.get("CONTROL_CODEX_HOME", "")
    if not home_raw:
        return ["CONTROL_CODEX_HOME is not set"]
    home = Path(home_raw).expanduser().resolve()
    auth = home / "auth.json"
    if not auth.exists():
        errors.append("native control auth.json is absent")
    config = home / "config.toml"
    if config.exists():
        lowered = config.read_text(encoding="utf-8", errors="replace").lower()
        for forbidden in ("openrouter", "parsewave", "model_provider", "model_providers", "openai_base_url"):
            if forbidden in lowered:
                errors.append(f"control config contains forbidden marker: {forbidden}")
    for name in ("OPENAI_BASE_URL", "OPENAI_API_BASE"):
        if env.get(name):
            errors.append(f"control environment contains {name}")
    return errors


def prepare_workspace(check: str, run_id: str, arm: str) -> Path:
    if check not in CHECK_DIRS or arm not in ARMS:
        raise ValueError("unknown check or arm")
    if check == "check3" and not check3_ready():
        raise RuntimeError("Check 3 is blocked: external team source lock is incomplete")
    source = CHECK_DIRS[check]
    workspace = ROOT / "workspaces" / check / run_id / arm
    if workspace.exists():
        raise FileExistsError(f"refusing to reuse workspace: {workspace}")
    workspace.mkdir(parents=True)
    if (source / "task.md").exists():
        shutil.copy2(source / "task.md", workspace / "task.md")
    if (source / "input").exists():
        shutil.copytree(source / "input", workspace / "input")
    if check == "check2":
        bindir = workspace / "bin"
        bindir.mkdir()
        helper = bindir / "vision-helper"
        helper.write_text(
            "#!/bin/sh\nexec \"${PYTHON:-python3}\" \"$VISION_HELPER_SCRIPT\" \"$@\"\n",
            encoding="utf-8",
        )
        helper.chmod(0o755)
    return workspace


def _base_child_env() -> dict[str, str]:
    allowed = ("PATH", "HOME", "USER", "SHELL", "LANG", "LC_ALL", "TMPDIR", "TERM")
    return {k: v for k, v in os.environ.items() if k in allowed}


def arm_command(arm: str, workspace: Path, prompt: str, env: dict[str, str]) -> tuple[list[str], dict[str, str]]:
    child = _base_child_env()
    if arm == "control_native_codex":
        errors = control_config_errors(env)
        if errors:
            raise RuntimeError("; ".join(errors))
        child["CODEX_HOME"] = str(Path(env["CONTROL_CODEX_HOME"]).expanduser())
        cmd = ["codex", "exec", "--ephemeral", "--json", "--skip-git-repo-check",
               "--sandbox", "workspace-write", "-C", str(workspace), prompt]
    elif arm == "exp_codexcli_deepseek":
        if not env.get("OPENROUTER_API_KEY"):
            raise RuntimeError("OPENROUTER_API_KEY is absent")
        child.update({"CODEX_HOME": str(ROOT / "state/codex-deepseek-home"),
                      "OPENROUTER_API_KEY": env["OPENROUTER_API_KEY"]})
        cmd = ["codex", "exec", "--ephemeral", "--json", "--skip-git-repo-check",
               "--sandbox", "workspace-write", "-C", str(workspace), prompt]
    elif arm == "exp_claudecode_deepseek":
        if not env.get("OPENROUTER_API_KEY"):
            raise RuntimeError("OPENROUTER_API_KEY is absent")
        child.update({
            "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
            "ANTHROPIC_AUTH_TOKEN": env["OPENROUTER_API_KEY"], "ANTHROPIC_API_KEY": "",
            "OPENROUTER_API_KEY": env["OPENROUTER_API_KEY"],
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": DEEPSEEK,
            "ANTHROPIC_DEFAULT_SONNET_MODEL": DEEPSEEK,
            "ANTHROPIC_DEFAULT_OPUS_MODEL": DEEPSEEK,
            "CLAUDE_CODE_SUBAGENT_MODEL": DEEPSEEK,
            "CLAUDE_CODE_SKIP_FAST_MODE_ORG_CHECK": "1",
            "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1",
            "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "1310720",
        })
        cmd = ["claude", "-p", "--model", DEEPSEEK, "--output-format", "stream-json",
               "--verbose", "--permission-mode", "bypassPermissions",
               "--no-session-persistence", prompt]
    else:
        raise ValueError(f"unknown arm: {arm}")
    child["TMPDIR"] = str(workspace / ".tmp")
    Path(child["TMPDIR"]).mkdir()
    if (workspace / "bin/vision-helper").exists():
        child.update({"VISION_HELPER_SCRIPT": str(ROOT / "tools/vision_helper.py"),
                      "VISION_DAEMON_URL": env.get("VISION_DAEMON_URL", "http://127.0.0.1:8765")})
    return cmd, child


def command_manifest(cmd: list[str], child_env: dict[str, str]) -> dict[str, Any]:
    return {"argv": cmd[:-1] + ["<EXACT_TASK_PROMPT>"],
            "environment_variable_names": sorted(child_env), "cwd_mode": "isolated_workspace"}


def run_process(cmd: list[str], cwd: Path, child_env: dict[str, str], timeout: int,
                stdout_path: Path, stderr_path: Path) -> dict[str, Any]:
    start_utc, start_ns = utc_now(), time.monotonic_ns()
    timed_out = False
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        proc = subprocess.Popen(cmd, cwd=cwd, env=child_env, stdout=out, stderr=err,
                                start_new_session=True)
        try:
            exit_code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            exit_code = proc.returncode
    end_ns = time.monotonic_ns()
    return {"start_utc": start_utc, "end_utc": utc_now(),
            "wall_seconds": round((end_ns - start_ns) / 1e9, 9),
            "timeout_seconds": timeout, "timed_out": timed_out, "exit_code": exit_code}


def deep_values(value: Any, key: str) -> list[Any]:
    found = []
    if isinstance(value, dict):
        for k, v in value.items():
            if k == key:
                found.append(v)
            found.extend(deep_values(v, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(deep_values(item, key))
    return found


def parse_usage_jsonl(path: Path) -> dict[str, Any]:
    events = []
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    aliases = {
        "input_tokens": ("input_tokens",), "cached_input_tokens": ("cached_input_tokens", "cache_read_input_tokens"),
        "cache_creation_input_tokens": ("cache_creation_input_tokens",), "output_tokens": ("output_tokens",),
        "reasoning_output_tokens": ("reasoning_output_tokens", "reasoning_tokens"),
        "total_tokens": ("total_tokens",), "reported_cost_usd": ("total_cost_usd", "cost_usd"),
    }
    output: dict[str, Any] = {key: None for key in aliases}
    for target, names in aliases.items():
        values = []
        for name in names:
            values.extend(v for event in events for v in deep_values(event, name) if isinstance(v, (int, float)))
        if values:
            output[target] = values[-1]
    models = [v for event in events for v in deep_values(event, "model") if isinstance(v, str)]
    output["actual_model"] = models[-1] if models else None
    return output


def summarize_vision_log(path: Path | None) -> dict[str, Any]:
    calls = []
    if path and path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                calls.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not calls:
        return {"calls": [], "totals": None}
    def total(field: str) -> int | float | None:
        values = [c.get(field) for c in calls]
        return sum(values) if values and all(isinstance(v, (int, float)) for v in values) else None
    return {"calls": calls, "totals": {"input_tokens": total("input_tokens"),
            "output_tokens": total("output_tokens"), "reported_cost_usd": total("reported_cost_usd")}}


def run_arm(check: str, arm: str, run_id: str, timeout: int | None = None,
            env_overrides: dict[str, str] | None = None, vision_log: Path | None = None) -> Path:
    if check == "check3" and not check3_ready():
        raise RuntimeError("Check 3 is blocked: external team source lock is incomplete")
    source = CHECK_DIRS[check]
    prompt_path = source / "task.md"
    if not prompt_path.exists():
        raise RuntimeError(f"task is not frozen for {check}")
    prompt = prompt_path.read_text(encoding="utf-8")
    workspace = prepare_workspace(check, run_id, arm)
    run_dir = ROOT / "runs" / check / run_id / arm
    run_dir.mkdir(parents=True, exist_ok=False)
    env = load_local_env()
    env.update(env_overrides or {})
    cmd, child = arm_command(arm, workspace, prompt, env)
    if timeout is None:
        timeout = 3600 if check != "check3" else int(parse_flat_yaml(source / "source.lock.yaml").get("timeout_seconds") or 0)
    if timeout <= 0:
        raise RuntimeError("Check 3 timeout is not configured")
    (run_dir / "task.md").write_bytes(prompt_path.read_bytes())
    write_json(run_dir / "input_manifest.json", tree_manifest(source / "input"))
    write_json(run_dir / "command.json", command_manifest(cmd, child))
    write_json(run_dir / "manifest.json", {"check_id": check, "run_id": run_id, "arm": arm,
               "created_utc": utc_now(), "task_sha256": sha256_file(prompt_path),
               "configured_model": "native_default" if arm == ARMS[0] else DEEPSEEK})
    write_json(run_dir / "start.json", {"start_utc": utc_now(), "timeout_seconds": timeout})
    (run_dir / "human_interventions.jsonl").touch()
    timing = run_process(cmd, workspace, child, timeout, run_dir / "stdout.jsonl", run_dir / "stderr.txt")
    write_json(run_dir / "end.json", timing)
    (run_dir / "exit_code.txt").write_text(str(timing["exit_code"]) + "\n", encoding="utf-8")
    write_json(run_dir / "usage.json", parse_usage_jsonl(run_dir / "stdout.jsonl"))
    write_json(run_dir / "vision_usage.json", summarize_vision_log(vision_log))
    final = workspace / "final"
    if final.exists():
        shutil.copytree(final, run_dir / "output")
    else:
        (run_dir / "output").mkdir()
    return run_dir


def run_id(prefix: str = "run") -> str:
    return f"{prefix}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(3)}"


def read_run_rows() -> list[dict[str, Any]]:
    rows = []
    for manifest_path in sorted((ROOT / "runs").glob("*/*/*/manifest.json")):
        run_dir = manifest_path.parent
        manifest = read_json(manifest_path, {})
        timing = read_json(run_dir / "end.json", {})
        usage = read_json(run_dir / "usage.json", {})
        vision = read_json(run_dir / "vision_usage.json", {})
        verifier = read_json(run_dir / "verifier.json", {})
        judge = read_json(run_dir / "judge.json", {})
        arm = manifest.get("arm")
        row = {key: None for key in METRIC_FIELDS}
        row.update({
            "check_id": manifest.get("check_id"), "run_id": manifest.get("run_id"), "arm": arm,
            "harness": "claude_code" if arm == ARMS[2] else "codex_cli",
            "configured_model": manifest.get("configured_model"), "actual_model": usage.get("actual_model"),
            "provider": "native_subscription" if arm == ARMS[0] else "openrouter",
            "status": "timeout" if timing.get("timed_out") else ("completed" if timing.get("exit_code") == 0 else "failed"),
            "exit_code": timing.get("exit_code"), "timed_out": timing.get("timed_out"),
            "wall_seconds": timing.get("wall_seconds"), "input_tokens": usage.get("input_tokens"),
            "cached_input_tokens": usage.get("cached_input_tokens"),
            "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "reasoning_output_tokens": usage.get("reasoning_output_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "main_model_reported_cost_usd": usage.get("reported_cost_usd"),
            "vision_calls": len(vision.get("calls", [])) if isinstance(vision.get("calls"), list) else None,
            "deterministic_score": verifier.get("score"),
            "official_verifier_pass": verifier.get("pass"), "official_verifier_score": verifier.get("official_score"),
            "judge_score": judge.get("score"),
            "human_interventions": sum(1 for x in (run_dir / "human_interventions.jsonl").read_text().splitlines() if x.strip()),
            "files_created": len(tree_manifest(run_dir / "output")),
        })
        vt = vision.get("totals") or {}
        row.update({"vision_input_tokens": vt.get("input_tokens"), "vision_output_tokens": vt.get("output_tokens"),
                    "vision_reported_cost_usd": vt.get("reported_cost_usd")})
        main_cost, vision_cost = row["main_model_reported_cost_usd"], row["vision_reported_cost_usd"]
        row["combined_reported_cost_usd"] = main_cost + vision_cost if main_cost is not None and vision_cost is not None else None
        rows.append(row)
    return rows


def write_results(rows: list[dict[str, Any]]) -> None:
    write_json(ROOT / "results/all_runs.json", rows)
    with (ROOT / "results/all_runs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def scan_secrets(paths: Iterable[Path]) -> list[dict[str, Any]]:
    findings = []
    excluded = {".git", ".venv", "__pycache__"}
    for base in paths:
        items = [base] if base.is_file() else base.rglob("*")
        for path in items:
            if not path.is_file() or excluded.intersection(path.parts):
                continue
            if path.name in {"auth.json", ".env.local"}:
                findings.append({"path": str(path), "reason": "forbidden credential filename"})
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if SECRET_VALUE_RE.search(text):
                findings.append({"path": str(path), "reason": "likely secret value"})
    return findings
