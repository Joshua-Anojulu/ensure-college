import pytest
from fastapi.testclient import TestClient

from app.data.loader import load_scholarships
from app.main import app

VALID_STUDENT = {
    "gpa": 3.8,
    "grade_level": "high_school_senior",
    "intended_majors": ["engineering"],
    "demographic_tags": ["first_generation"],
    "state": "CA",
    "citizenship": "us_citizen",
    "financial_need_level": "high",
    "activities": ["robotics club"],
}

REALISTIC_STUDENT = {
    "gpa": 4.0,
    "grade_level": "high_school_senior",
    "intended_majors": ["science"],
    "demographic_tags": ["african_american"],
    "state": "TX",
    "citizenship": "us_citizen",
    "financial_need_level": "unspecified",
    "activities": [],
}

MATCH_RESULT_FIELDS = {
    "scholarship_id",
    "score",
    "match_reasons",
    "score_breakdown",
    "verified",
    "closing_soon",
    "match_tier",
}

VOCABULARY_FIELDS = {
    "grade_level",
    "citizenship",
    "demographic_tags",
    "fields_of_study",
    "state",
}


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestFrontend:
    def test_index_page_served(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Scholarships4U" in response.text
        assert "/static/js/app.js" in response.text


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestVocabularyEndpoint:
    def test_vocabulary_returns_constrained_option_lists(self, client):
        response = client.get("/vocabulary")
        assert response.status_code == 200
        data = response.json()
        for field in VOCABULARY_FIELDS:
            assert field in data
            assert isinstance(data[field], list)
            assert len(data[field]) > 0
            for option in data[field]:
                assert "label" in option
                assert "value" in option


class TestScholarshipsEndpoint:
    def test_scholarships_returns_loaded_dataset(self, client):
        expected_count = len(load_scholarships())
        response = client.get("/scholarships")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == expected_count
        assert len(data) > 0


class TestMatchEndpoint:
    def test_match_with_valid_profile_returns_ranked_results(self, client):
        response = client.post("/match", json=VALID_STUDENT)
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) > 0
        for result in results:
            assert MATCH_RESULT_FIELDS.issubset(result.keys())
            assert isinstance(result["match_reasons"], list)
            assert isinstance(result["score_breakdown"], dict)
            assert isinstance(result["verified"], bool)
            assert isinstance(result["closing_soon"], bool)

    def test_match_with_realistic_vocabulary_profile_returns_qualifying_scholarships(
        self, client
    ):
        response = client.post("/match", json=REALISTIC_STUDENT)
        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0
        scores = [result["score"] for result in results]
        assert len(set(scores)) > 1
        assert results[0]["scholarship_id"] == "regeneron-sts"
        assert results[1]["scholarship_id"] == "ron-brown-scholar"
        assert results[0]["score"] > results[1]["score"]
        assert results[0]["match_tier"] == "strong"
        tied_at_ten = [r for r in results if r["score"] == 10.0]
        if len(tied_at_ten) > 1:
            names = [r["scholarship_name"] for r in tied_at_ten]
            assert names == sorted(names, key=str.lower)

    def test_match_results_sorted_by_score_descending(self, client):
        response = client.post("/match", json=VALID_STUDENT)
        assert response.status_code == 200
        scores = [result["score"] for result in response.json()]
        assert scores == sorted(scores, reverse=True)

    def test_match_with_invalid_gpa_returns_422(self, client):
        invalid_student = {**VALID_STUDENT, "gpa": 5.0}
        response = client.post("/match", json=invalid_student)
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("gpa" in str(error).lower() for error in detail)

    def test_match_with_missing_required_field_returns_422(self, client):
        invalid_student = {key: value for key, value in VALID_STUDENT.items() if key != "grade_level"}
        response = client.post("/match", json=invalid_student)
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("grade_level" in str(error).lower() for error in detail)

    def test_match_with_unknown_grade_level_returns_422(self, client):
        invalid_student = {**VALID_STUDENT, "grade_level": "grade_12"}
        response = client.post("/match", json=invalid_student)
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert any("grade_level" in str(error).lower() for error in detail)
