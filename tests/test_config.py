"""Tests for production configuration safety (session secret resolution)."""

import pytest

from app.main import DEV_SESSION_SECRET, _resolve_session_secret, is_production_deploy


def test_production_requires_session_secret(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        _resolve_session_secret()


def test_production_rejects_dev_default(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("SESSION_SECRET", DEV_SESSION_SECRET)
    with pytest.raises(RuntimeError):
        _resolve_session_secret()


def test_postgres_url_counts_as_production(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        _resolve_session_secret()


def test_production_accepts_real_secret(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("SESSION_SECRET", "a-strong-unique-secret")
    assert _resolve_session_secret() == "a-strong-unique-secret"


def test_local_falls_back_to_dev_default(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///local.db")
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    assert _resolve_session_secret() == DEV_SESSION_SECRET


def test_is_production_deploy_on_render(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert is_production_deploy() is True


def test_is_production_deploy_on_postgres_url(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")
    assert is_production_deploy() is True


def test_is_production_deploy_false_locally(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///local.db")
    assert is_production_deploy() is False
