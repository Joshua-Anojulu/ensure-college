import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.scholarship import ApplicationRequirement, EssayPromptItem, EssayPrompts


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestEssayPromptsModel:
    def test_public_prompts_round_trip(self):
        req = ApplicationRequirement(
            id="essays",
            label="Complete the essays",
            essay_prompts={
                "status": "public",
                "items": [{"prompt": "Describe a community you belong to.", "length": "150-250 words"}],
            },
        )
        assert req.essay_prompts.status == "public"
        assert req.essay_prompts.items[0].prompt.startswith("Describe")
        assert req.essay_prompts.items[0].length == "150-250 words"

    def test_requirement_without_prompts_stays_none(self):
        req = ApplicationRequirement(id="apply", label="Apply online")
        assert req.essay_prompts is None

    def test_public_requires_at_least_one_item(self):
        with pytest.raises(ValidationError):
            EssayPrompts(status="public", items=[])

    def test_gated_requires_empty_items(self):
        with pytest.raises(ValidationError):
            EssayPrompts(status="gated", items=[EssayPromptItem(prompt="x")])

    def test_gated_with_empty_items_is_valid(self):
        prompts = EssayPrompts(status="gated", items=[])
        assert prompts.status == "gated"

    def test_unknown_status_rejected(self):
        with pytest.raises(ValidationError):
            EssayPrompts(status="varies", items=[])

    def test_blank_prompt_text_rejected(self):
        with pytest.raises(ValidationError):
            EssayPromptItem(prompt="   ")


class TestDetailPagePrompts:
    def _first_scholarship_with_requirements(self, client):
        state = client.app.state
        for entry in state.scholarships:
            if entry.application_requirements:
                return entry
        pytest.skip("no scholarship with requirements in catalog")

    def test_public_prompts_render_in_details_element(self, client):
        entry = self._first_scholarship_with_requirements(client)
        entry.application_requirements[0].essay_prompts = EssayPrompts(
            status="public",
            items=[EssayPromptItem(prompt="Why does this scholarship matter to you?", length="500 words max")],
        )
        try:
            response = client.get(f"/scholarships/{entry.id}")
            assert response.status_code == 200
            assert "<details" in response.text
            assert "Why does this scholarship matter to you?" in response.text
            assert "500 words max" in response.text
        finally:
            entry.application_requirements[0].essay_prompts = None

    def test_gated_prompts_render_muted_line(self, client):
        entry = self._first_scholarship_with_requirements(client)
        entry.application_requirements[0].essay_prompts = EssayPrompts(status="gated", items=[])
        try:
            response = client.get(f"/scholarships/{entry.id}")
            assert response.status_code == 200
            assert "Prompts revealed after registration" in response.text
        finally:
            entry.application_requirements[0].essay_prompts = None


from pathlib import Path

APP_JS = Path(__file__).resolve().parent.parent / "app" / "static" / "js" / "app.js"


class TestFrontendPromptWiring:
    def test_app_js_defines_prompt_block_and_start_by(self):
        source = APP_JS.read_text(encoding="utf-8")
        assert "function buildPromptBlock" in source
        assert "function essayStartByLabel" in source
        assert "Prompts revealed after registration" in source
        assert "Start drafting by" in source
