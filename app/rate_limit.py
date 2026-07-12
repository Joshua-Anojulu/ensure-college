"""A small in-memory rate limiter used as a FastAPI dependency.

State lives in the process, which is enough for a single-instance demo deploy. A
shared store (for example Redis) would be the next step for multi-instance hosting.
Set RATE_LIMIT_ENABLED=false to turn it off (the test suite does this).
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from urllib.request import Request as _UrlRequest, urlopen

from fastapi import HTTPException, Request, status


def _enabled() -> bool:
    return os.getenv("RATE_LIMIT_ENABLED", "true").lower() not in {"0", "false", "no"}


def _upstash_configured() -> bool:
    return bool(
        os.getenv("UPSTASH_REDIS_REST_URL", "").strip()
        and os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    )


def _upstash_incr(key: str, window_seconds: float) -> int:
    """Fixed-window counter in Upstash Redis over its REST API.

    Increments a per-window bucket key and sets its TTL so old windows expire.
    Returns the current count. Raises on transport errors (caller fails open).
    """
    base = os.getenv("UPSTASH_REDIS_REST_URL", "").strip().rstrip("/")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    bucket = int(time.time() // window_seconds)
    rkey = f"rl:{key}:{bucket}"
    body = json.dumps([["INCR", rkey], ["EXPIRE", rkey, int(window_seconds)]]).encode("utf-8")
    req = _UrlRequest(
        f"{base}/pipeline",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=3) as resp:
        results = json.loads(resp.read().decode("utf-8"))
    return int(results[0]["result"])


class RateLimiter:
    """Sliding-window limiter: at most ``max_requests`` per ``window_seconds`` per key."""

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        hits = self._hits[key]
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return False
        hits.append(now)
        return True

    def clear(self) -> None:
        self._hits.clear()


def _client_ip(request: Request) -> str:
    """Best-effort client IP for rate-limit keying.

    Behind Vercel/Render the socket peer is the proxy, so every user would share
    one bucket. Those platforms set X-Forwarded-For themselves (client-supplied
    values are overwritten at the edge), so its first hop is trustworthy there.
    Locally there is no proxy and the header is absent, falling back to the peer.
    """
    headers = getattr(request, "headers", None)
    forwarded = headers.get("x-forwarded-for", "") if headers is not None else ""
    if forwarded:
        first_hop = forwarded.split(",")[0].strip()
        if first_hop:
            return first_hop
    return request.client.host if request.client else "unknown"


_fallback_warned = False


def rate_limiter(max_requests: int, window_seconds: float, scope: str):
    """Build a dependency that enforces a per-client-IP limit for one scope."""

    limiter = RateLimiter(max_requests, window_seconds)

    def dependency(request: Request) -> None:
        global _fallback_warned
        if not _enabled():
            return
        key = f"{scope}:{_client_ip(request)}"
        if _upstash_configured():
            try:
                allowed = _upstash_incr(key, window_seconds) <= max_requests
            except (OSError, ValueError, KeyError):
                allowed = True  # fail open: never lock users out on a Redis blip
        else:
            # On serverless the in-memory store is per-instance and resets on
            # cold start, so limits are effectively void — say so once rather
            # than degrade silently when the Upstash env vars go missing.
            if not _fallback_warned and os.getenv("DATABASE_URL", "").startswith("postgres"):
                print("[rate-limit] Upstash not configured; falling back to per-instance in-memory limiter", flush=True)
                _fallback_warned = True
            allowed = limiter.allow(key)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "Too many requests. Please wait a moment and try again."},
            )

    dependency.limiter = limiter
    return dependency
