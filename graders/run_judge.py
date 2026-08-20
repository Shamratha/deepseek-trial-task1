#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path

from infra_lib import load_local_env


def post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    env, packet = load_local_env(), json.loads(args.packet.read_text())
    prompt = "Blindly grade this artifact packet. Return only valid JSON matching required_response.\n" + json.dumps(packet)
    mode = env.get("JUDGE_MODE", "athena")
    if mode == "athena":
        base, key, model = env.get("ATHENA_BASE_URL"), env.get("ATHENA_API_KEY"), env.get("ATHENA_MODEL")
        if not all((base, key, model)):
            raise SystemExit("Athena judge configuration incomplete")
        response = post_json(base.rstrip("/") + "/v1/chat/completions",
                             {"model": model, "messages": [{"role": "user", "content": prompt}],
                              "response_format": {"type": "json_object"}},
                             {"Authorization": f"Bearer {key}"})
        text = response["choices"][0]["message"]["content"]
    elif mode == "gemini":
        key, model = env.get("GEMINI_API_KEY"), env.get("GEMINI_JUDGE_MODEL", "gemini-3.7-flash")
        if not key:
            raise SystemExit("Gemini judge configuration incomplete")
        response = post_json(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                             {"contents": [{"parts": [{"text": prompt}]}],
                              "generationConfig": {"responseMimeType": "application/json"}}, {})
        text = response["candidates"][0]["content"]["parts"][0]["text"]
    else:
        raise SystemExit(f"unsupported judge mode: {mode}")
    print(json.dumps(json.loads(text), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
