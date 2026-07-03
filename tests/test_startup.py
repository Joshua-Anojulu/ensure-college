import importlib


def test_startup_skips_migrations_when_disabled(monkeypatch):
    monkeypatch.setenv("RUN_MIGRATIONS_ON_STARTUP", "false")
    import app.main as main
    called = {"n": 0}
    monkeypatch.setattr(main, "init_db", lambda: called.__setitem__("n", called["n"] + 1))
    # Drive the lifespan startup manually.
    import anyio

    async def run():
        async with main.lifespan(main.app):
            pass

    anyio.run(run)
    assert called["n"] == 0
