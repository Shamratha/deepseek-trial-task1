#!/usr/bin/env python3
"""Setup probes; native control remains explicit opt-in."""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from infra_lib import ARMS, ROOT, arm_command, load_local_env, parse_usage_jsonl, run_process, utc_now, write_json


def probe(arm: str, expected: str, env: dict[str, str]) -> dict:
    with tempfile.TemporaryDirectory(prefix="harness-smoke-") as temp:
        workspace = Path(temp)
        prompt = f"Reply with exactly {expected}. Then create probe.txt containing exactly FILE_WRITE_OK and read it back."
        cmd, child = arm_command(arm, workspace, prompt, env)
        out, err = workspace / "stdout.jsonl", workspace / "stderr.txt"
        timing = run_process(cmd, workspace, child, 300, out, err)
        raw = out.read_text(encoding="utf-8", errors="replace")
        return {"arm": arm, "timing": timing, "expected_reply_seen": expected in raw,
                "file_probe_ok": (workspace / "probe.txt").exists() and (workspace / "probe.txt").read_text().strip() == "FILE_WRITE_OK",
                "usage": parse_usage_jsonl(out), "stderr_nonempty": bool(err.read_text(errors="replace").strip())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deepseek-codex", action="store_true")
    parser.add_argument("--deepseek-claude", action="store_true")
    parser.add_argument("--control", action="store_true", help="explicitly consume a tiny native setup smoke call")
    parser.add_argument("--vision", action="store_true", help="run local-file and HTTPS vision sidecar probes")
    args = parser.parse_args()
    if not any(vars(args).values()):
        args.deepseek_codex = args.deepseek_claude = args.vision = True
    env, results = load_local_env(), []
    if (args.deepseek_codex or args.deepseek_claude) and not env.get("OPENROUTER_API_KEY"):
        raise SystemExit("DeepSeek smoke requires OPENROUTER_API_KEY")
    if args.vision:
        configured_model = env.get("VISION_MODEL")
        if not configured_model:
            for line in (ROOT / "config/vision.yaml").read_text().splitlines():
                if line.strip().startswith("model:"):
                    value = line.split(":", 1)[1].strip().strip("'\"")
                    configured_model = None if value in ("", "null", "~") else value
        if not configured_model or not env.get("VISION_OPENROUTER_API_KEY"):
            raise SystemExit("Vision smoke requires VISION_MODEL and VISION_OPENROUTER_API_KEY")
    if args.deepseek_codex:
        results.append(probe(ARMS[1], "DEEPSEEK_CODEX_ROUTE_OK", env))
    if args.deepseek_claude:
        results.append(probe(ARMS[2], "DEEPSEEK_CLAUDE_ROUTE_OK", env))
    if args.control:
        result = probe(ARMS[0], "NATIVE_CODEX_ROUTE_OK", env)
        result["label"] = "setup_smoke_not_measured"
        results.append(result)
    if args.vision:
        model = env.get("VISION_MODEL")
        if not model:
            for line in (ROOT / "config/vision.yaml").read_text().splitlines():
                if line.strip().startswith("model:"):
                    value = line.split(":", 1)[1].strip().strip("'\"")
                    model = None if value in ("", "null", "~") else value
        with tempfile.TemporaryDirectory(prefix="vision-smoke-") as temp:
            temp_path = Path(temp)
            local_image = temp_path / "pixel.png"
            local_image.write_bytes(base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="))
            vision_log = temp_path / "vision.jsonl"
            child = dict(os.environ)
            child.update({"VISION_MODEL": model, "VISION_OPENROUTER_API_KEY": env["VISION_OPENROUTER_API_KEY"]})
            daemon = subprocess.Popen([sys.executable, str(ROOT / "tools/vision_daemon.py"), "--port", "0",
                                       "--log", str(vision_log)], text=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, env=child)
            try:
                ready = json.loads(daemon.stdout.readline())
                helper_env = dict(os.environ)
                helper_env["VISION_DAEMON_URL"] = f"http://127.0.0.1:{ready['port']}"
                url = next(x for x in (ROOT / "benchmarks/check2_visual_artifact/input/image_candidates.txt").read_text().splitlines() if x)
                probes = []
                for source_args in (["--file", str(local_image)], ["--url", url]):
                    proc = subprocess.run([sys.executable, str(ROOT / "tools/vision_helper.py"), *source_args,
                                           "--question", "Briefly identify this image."], text=True,
                                          capture_output=True, env=helper_env, timeout=180)
                    probes.append({"source": source_args[0][2:], "exit_code": proc.returncode,
                                   "response": proc.stdout.strip(), "stderr": proc.stderr.strip()})
                results.append({"vision": {"model": model, "probes": probes,
                                "raw_usage": [json.loads(x) for x in vision_log.read_text().splitlines()]}})
            finally:
                daemon.terminate()
                daemon.wait(timeout=5)
    path = ROOT / "results" / f"setup_smoke_{utc_now().replace(':', '').replace('-', '')}.json"
    write_json(path, results)
    print(path)


if __name__ == "__main__":
    main()
