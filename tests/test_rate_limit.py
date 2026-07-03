import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.rate_limit import RateLimiter


class TestRateLimiterUnit:
    def test_allows_up_to_max_then_blocks(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False

    def test_keys_are_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.allow("a") is True
        assert limiter.allow("b") is True
        assert limiter.allow("a") is False

    def test_clear_resets(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.allow("k") is True
        assert limiter.allow("k") is False
        limiter.clear()
        assert limiter.allow("k") is True


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestRateLimitEndpoint:
    def test_login_returns_429_when_over_limit(self, client, monkeypatch):
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
        from app.api.auth_routes import _login_limit

        _login_limit.limiter.clear()
        monkeypatch.setattr(_login_limit.limiter, "max_requests", 2)
        payload = {"email": "nobody@example.com", "password": "password123"}
        try:
            assert client.post("/auth/login", json=payload).status_code == 401
            assert client.post("/auth/login", json=payload).status_code == 401
            assert client.post("/auth/login", json=payload).status_code == 429
        finally:
            _login_limit.limiter.clear()

    def test_delete_account_returns_429_when_over_limit(self, client, monkeypatch):
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
        from app.api.auth_routes import _delete_limit

        _delete_limit.limiter.clear()
        monkeypatch.setattr(_delete_limit.limiter, "max_requests", 1)
        try:
            # The limiter runs before the authentication dependency, so this
            # does not need a real account to verify the endpoint is protected.
            assert client.post("/auth/delete-account", json={"password": "password123"}).status_code == 401
            assert client.post("/auth/delete-account", json={"password": "password123"}).status_code == 429
        finally:
            _delete_limit.limiter.clear()


def test_upstash_path_blocks_over_limit(monkeypatch):
    import app.rate_limit as rl
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://example.upstash.io")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "tok")
    calls = {"n": 0}

    def fake_incr(key, window_seconds):
        calls["n"] += 1
        return calls["n"]  # 1, 2, 3, ...

    monkeypatch.setattr(rl, "_upstash_incr", fake_incr)
    dep = rl.rate_limiter(2, 60, "test")

    class Req:
        class client:
            host = "1.2.3.4"

    dep(Req())  # 1 -> ok
    dep(Req())  # 2 -> ok
    with pytest.raises(HTTPException):
        dep(Req())  # 3 -> blocked


def test_upstash_fail_open(monkeypatch):
    import app.rate_limit as rl
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://example.upstash.io")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "tok")

    def boom(key, window_seconds):
        raise OSError("redis down")

    monkeypatch.setattr(rl, "_upstash_incr", boom)
    dep = rl.rate_limiter(1, 60, "test")

    class Req:
        class client:
            host = "9.9.9.9"

    dep(Req()); dep(Req())  # must NOT raise (fail open)
