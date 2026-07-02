"""Shared test setup.

Point the app at an isolated, temporary SQLite database before any app module
is imported, so tests never touch a real local or production database.
"""

import atexit
import os
import tempfile

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)

# SQLAlchemy SQLite URLs use forward slashes even on Windows.
os.environ["DATABASE_URL"] = "sqlite:///" + _db_path.replace("\\", "/")
os.environ.setdefault("SESSION_SECRET", "test-session-secret")
# Disable rate limiting by default so the suite is not throttled. The dedicated
# rate-limit test re-enables it for itself.
os.environ["RATE_LIMIT_ENABLED"] = "false"

# Tests assert the request-derived fallback base URL (http://testserver), so
# never let an ambient PUBLIC_APP_URL (e.g. from a local .env) leak in and make
# production-hygiene assertions depend on the developer's environment. Set it to
# empty (not pop) so the later load_dotenv() in app.main cannot re-populate it.
os.environ["PUBLIC_APP_URL"] = ""


@atexit.register
def _cleanup_test_db() -> None:
    try:
        os.remove(_db_path)
    except OSError:
        pass
