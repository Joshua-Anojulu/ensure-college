"""Tests for server-rendered SEO pages (detail, browse, sitemap)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestSlugIndexes:
    def test_state_has_slug_lookup_dicts(self, client):
        state = client.app.state
        assert state.scholarships_by_id["coca-cola-scholars"].name == "Coca-Cola Scholars Program"
        assert len(state.scholarships_by_id) == len(state.scholarships)
        assert len(state.programs_by_id) == len(state.programs)
        assert len(state.competitions_by_id) == len(state.competitions)
