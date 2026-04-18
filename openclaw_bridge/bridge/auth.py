from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request

from .settings import settings


@dataclass
class ReplayCache:
    ttl_seconds: int

    def __post_init__(self) -> None:
        self._items: dict[str, float] = {}

    def seen_or_add(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.ttl_seconds
        stale_keys = [k for k, ts in self._items.items() if ts < cutoff]
        for stale in stale_keys:
            self._items.pop(stale, None)

        if key in self._items:
            return True

        self._items[key] = now
        return False


replay_cache = ReplayCache(ttl_seconds=settings.nonce_ttl_seconds)


def _body_hash(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _canonical_payload(method: str, path: str, timestamp: str, nonce: str, body: bytes) -> str:
    return "\n".join([method.upper(), path, timestamp, nonce, _body_hash(body)])


def _signature(payload: str) -> str:
    return hmac.new(settings.hmac_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


async def verify_request_signature(request: Request) -> str:
    key_id = request.headers.get("X-Key-Id", "")
    timestamp = request.headers.get("X-Timestamp", "")
    nonce = request.headers.get("X-Nonce", "")
    signature = request.headers.get("X-Signature", "")

    if not all([key_id, timestamp, nonce, signature]):
        raise HTTPException(status_code=401, detail="Missing auth headers")

    if key_id != settings.hmac_key_id:
        raise HTTPException(status_code=401, detail="Invalid key id")

    try:
        ts = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid timestamp") from exc

    now = int(time.time())
    if abs(now - ts) > settings.auth_max_skew_seconds:
        raise HTTPException(status_code=401, detail="Request timestamp out of allowed skew")

    replay_id = f"{key_id}:{timestamp}:{nonce}"
    if replay_cache.seen_or_add(replay_id):
        raise HTTPException(status_code=401, detail="Replay detected")

    body = await request.body()
    payload = _canonical_payload(request.method, request.url.path, timestamp, nonce, body)
    expected = _signature(payload)

    if not hmac.compare_digest(signature.lower(), expected.lower()):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return key_id
