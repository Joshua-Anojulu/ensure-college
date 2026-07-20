"""End-to-end harness: a real browser against a real server on a throwaway DB.

Runs the app in-process on a random port with its own SQLite file, so the
suite never touches the dev database and never needs the network.
"""
import os
import socket
import tempfile
import threading
import time
from pathlib import Path

import pytest
import uvicorn


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server():
    tmp = Path(tempfile.mkdtemp(prefix="ec-e2e-"))
    db = tmp / "e2e.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db}"
    os.environ["SESSION_SECRET"] = "e2e-only-secret-not-production-000000000000"
    os.environ["RUN_MIGRATIONS_ON_STARTUP"] = "true"
    os.environ["AI_FEATURES_ENABLED"] = "false"

    from app.main import app  # imported after env is set

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 30
    while not server.started and time.time() < deadline:
        time.sleep(0.1)
    if not server.started:
        raise RuntimeError("server did not start")

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1440, "height": 900}}


# The anonymous session probe on load answers 401 by design (no cookie yet);
# Chrome logs every failed fetch as a console error. That one is expected.
BENIGN = ("401 (Unauthorized)",)


def _is_real_error(text: str) -> bool:
    return not any(b in text for b in BENIGN)


def _attach_console_errors(page):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on(
        "console",
        lambda m: errors.append(m.text)
        if (m.type == "error" and _is_real_error(m.text))
        else None,
    )
    page.console_errors = errors


@pytest.fixture
def page(page, live_server):
    """A page with the age gate already accepted and console errors captured."""
    _attach_console_errors(page)
    page.goto(live_server, wait_until="domcontentloaded")
    gate = page.locator("#age-gate")
    if gate.count() and gate.is_visible():
        page.check("#age-gate-agree")
        page.click("#age-gate-continue")
        gate.wait_for(state="hidden", timeout=5000)
    return page


@pytest.fixture
def cold_page(browser, live_server):
    """A fresh landing page that does not auto-dismiss the age gate."""
    context = browser.new_context(viewport={"width": 412, "height": 823}, device_scale_factor=1.75)
    page = context.new_page()
    _attach_console_errors(page)
    page.goto(live_server, wait_until="domcontentloaded")
    yield page
    context.close()


@pytest.fixture
def accepted_page(browser, live_server):
    """A landing page with consent present before the first document script runs."""
    context = browser.new_context(viewport={"width": 412, "height": 823}, device_scale_factor=1.75)
    context.add_init_script("window.localStorage.setItem('site_consent_v1', 'yes');")
    page = context.new_page()
    _attach_console_errors(page)
    page.goto(live_server, wait_until="domcontentloaded")
    yield page
    context.close()


def unique_email() -> str:
    return f"e2e-{int(time.time() * 1000)}@example.com"
