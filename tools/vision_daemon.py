#!/usr/bin/env python3
"""Loopback-only OpenRouter vision sidecar; owns the credential and usage log."""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


def now_utc() -> str:
    import datetime as dt
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def vision_model_from_config() -> str | None:
    config = Path(__file__).resolve().parents[1] / "config/vision.yaml"
    for line in config.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("model:"):
            value = line.split(":", 1)[1].strip().strip("'\"")
            return None if value in ("", "null", "~") else value
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = "VisionSidecar/1.0"

    def log_message(self, *_: Any) -> None:
        return

    def reply(self, code: int, value: dict[str, Any]) -> None:
        raw = json.dumps(value).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.reply(200, {"ok": True, "model": self.server.model})
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self) -> None:
        started = time.monotonic_ns()
        event: dict[str, Any] = {"timestamp_utc": now_utc(), "model": self.server.model,
                                 "success": False, "response_id": None, "input_tokens": None,
                                 "output_tokens": None, "reported_cost_usd": None}
        try:
            if self.path != "/v1/vision":
                raise ValueError("not found")
            size = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(size))
            question = str(request.get("question", "")).strip()
            source_kind = request.get("source_kind")
            event["source"] = request.get("source_label")
            if source_kind == "url":
                image_url = request.get("url")
                if not isinstance(image_url, str) or not image_url.startswith("https://"):
                    raise ValueError("vision URLs must use HTTPS")
            elif source_kind == "data":
                image_url = request.get("data_url")
                if not isinstance(image_url, str) or not image_url.startswith("data:image/"):
                    raise ValueError("invalid local image data")
            else:
                raise ValueError("source_kind must be url or data")
            payload = {"model": self.server.model, "messages": [{"role": "user", "content": [
                {"type": "text", "text": question}, {"type": "image_url", "image_url": {"url": image_url}}
            ]}]}
            upstream = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode(), method="POST",
                headers={"Authorization": f"Bearer {self.server.api_key}", "Content-Type": "application/json",
                         "HTTP-Referer": "https://localhost/deepseek-v4-harness-eval",
                         "X-Title": "DeepSeek V4 Harness Evaluation"},
            )
            with urllib.request.urlopen(upstream, timeout=120) as response:
                body = json.loads(response.read())
            usage = body.get("usage") or {}
            answer = body["choices"][0]["message"]["content"]
            event.update({"success": True, "response_id": body.get("id"),
                          "input_tokens": usage.get("prompt_tokens"),
                          "output_tokens": usage.get("completion_tokens"),
                          "reported_cost_usd": usage.get("cost")})
            self.reply(200, {"answer": answer, "model": body.get("model"), "response_id": body.get("id")})
        except urllib.error.HTTPError as exc:
            event["error"] = f"upstream HTTP {exc.code}"
            self.reply(502, {"error": event["error"]})
        except Exception as exc:
            event["error"] = f"{type(exc).__name__}: {exc}"
            self.reply(400 if isinstance(exc, ValueError) else 500, {"error": event["error"]})
        finally:
            event["duration_seconds"] = round((time.monotonic_ns() - started) / 1e9, 9)
            with self.server.log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--log", type=Path, default=Path("state/vision-usage.jsonl"))
    args = parser.parse_args()
    if args.bind not in ("127.0.0.1", "::1", "localhost"):
        raise SystemExit("refusing non-loopback bind")
    model = os.environ.get("VISION_MODEL") or vision_model_from_config()
    api_key = os.environ.get("VISION_OPENROUTER_API_KEY")
    if not model or not api_key:
        raise SystemExit("VISION_MODEL and VISION_OPENROUTER_API_KEY are required")
    args.log.parent.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    server.model, server.api_key, server.log_path = model, api_key, args.log
    print(json.dumps({"ready": True, "bind": args.bind, "port": server.server_address[1], "model": model}), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
