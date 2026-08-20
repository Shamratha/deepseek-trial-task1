#!/usr/bin/env python3
"""Credential-free client exposed to all Check 2 workspaces."""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url")
    source.add_argument("--file", type=Path)
    parser.add_argument("--question", required=True)
    args = parser.parse_args()
    if args.url:
        if not args.url.startswith("https://"):
            raise SystemExit("only HTTPS image URLs are allowed")
        payload = {"source_kind": "url", "url": args.url, "source_label": args.url,
                   "question": args.question}
    else:
        path = args.file.resolve()
        data = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        if not mime.startswith("image/"):
            raise SystemExit("local file does not have an image MIME type")
        payload = {"source_kind": "data", "data_url": f"data:{mime};base64,{base64.b64encode(data).decode()}",
                   "source_label": path.name, "question": args.question}
    base = os.environ.get("VISION_DAEMON_URL", "http://127.0.0.1:8765").rstrip("/")
    request = urllib.request.Request(base + "/v1/vision", data=json.dumps(payload).encode(),
                                     method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=150) as response:
        result = json.loads(response.read())
    print(result["answer"])


if __name__ == "__main__":
    main()
