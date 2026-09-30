#!/usr/bin/env python3
"""Expose OpenClaw Bridge's signed HTTP endpoint as a local stdio MCP server."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


def _config() -> tuple[str, str, str]:
    url = os.environ.get("OPENCLAW_BRIDGE_URL", "").strip()
    key_id = os.environ.get("OPENCLAW_BRIDGE_KEY_ID", "").strip()
    secret_file = os.environ.get("OPENCLAW_BRIDGE_SECRET_FILE", "").strip()
    secret = (
        Path(secret_file).read_text(encoding="utf-8").strip()
        if secret_file
        else os.environ.get("OPENCLAW_BRIDGE_HMAC_SECRET", "").strip()
    )
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or not parsed.path.endswith("/openclaw_bridge.api.mcp"):
        raise ValueError("OPENCLAW_BRIDGE_URL must be the HTTPS MCP RPC endpoint")
    if not key_id or not secret:
        raise ValueError("Bridge key ID and HMAC secret are required")
    return url, key_id, secret


def _forward(message: dict, url: str, key_id: str, secret: str) -> dict:
    body = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    path = urlsplit(url).path
    canonical = "\n".join(
        ["POST", path, timestamp, nonce, hashlib.sha256(body).hexdigest()]
    )
    signature = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Key-Id": key_id,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Signature": signature,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main() -> int:
    try:
        url, key_id, secret = _config()
    except (OSError, ValueError) as exc:
        print(f"OpenClaw Bridge configuration error: {exc}", file=sys.stderr)
        return 2

    for line in sys.stdin:
        message = None
        try:
            message = json.loads(line)
            if not isinstance(message, dict):
                continue
            # MCP notifications have no response. The remote bridge has no
            # session state, so forwarding them is unnecessary.
            if "id" not in message:
                continue
            result = _forward(message, url, key_id, secret)
        except (json.JSONDecodeError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            request_id = message.get("id") if isinstance(message, dict) else None
            result = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": f"Bridge request failed: {exc}"},
            }
        sys.stdout.write(json.dumps(result, separators=(",", ":"), ensure_ascii=False) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
