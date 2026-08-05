import json
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.api.routes.metadata import get_repository

client = TestClient(app)


def test_full_health_and_metadata_flow():
    """
    Verifies that the FastAPI application initializes properly and serves health & metadata.
    """
    # 1. Health check
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json() == {"status": "ok"}

    # 2. Cities metadata
    cities_resp = client.get("/metadata/cities")
    assert cities_resp.status_code == 200
    cities = cities_resp.json().get("cities", [])
    assert len(cities) > 0

    first_city = cities[0]

    # 3. Locations metadata
    locations_resp = client.get(f"/metadata/locations?city={first_city}")
    assert locations_resp.status_code == 200
    locations = locations_resp.json().get("locations", [])
    assert isinstance(locations, list)

    # 4. Cuisines metadata
    cuisines_resp = client.get("/metadata/cuisines")
    assert cuisines_resp.status_code == 200
    cuisines = cuisines_resp.json().get("cuisines", [])
    assert len(cuisines) > 0


def test_recommendations_integration_end_to_end(monkeypatch):
    """
    End-to-end integration test of POST /recommendations endpoint.
    Tests preference parsing, repository candidate filtering, mock LLM response ranking,
    hallucination guarding, and response formatting.
    """
    from src.services.filter_service import FilterService
    from src.models.preferences import UserPreferences

    repo = get_repository()
    cities = repo.get_cities()
    target_city = cities[0]

    prefs = UserPreferences(city=target_city, top_k=5, additional_notes="Looking for nice ambiance and great food")
    filter_service = FilterService(repo)
    candidates, _, _ = filter_service.filter_restaurants(prefs)
    assert len(candidates) >= 2

    r1, r2 = candidates[0], candidates[1]

    # Mock response from LLM returning valid restaurant IDs
    mock_llm_json = json.dumps({
        "recommendations": [
            {
                "restaurant_id": r1.id,
                "rank": 1,
                "explanation": f"Top match: {r1.name} offers authentic taste and excellent environment."
            },
            {
                "restaurant_id": r2.id,
                "rank": 2,
                "explanation": f"Great alternative: {r2.name} is highly rated."
            }
        ],
        "summary": f"Selected top 2 spots in {target_city} based on your preferences."
    })

    # Monkeypatch LLM completion to return mock_llm_json
    async def mock_generate_completion(self, sys_prompt, user_prompt):
        return mock_llm_json

    from src.llm.client import MockLLMClient
    monkeypatch.setattr(MockLLMClient, "generate_completion", mock_generate_completion)
    monkeypatch.setattr("src.config.settings.LLM_PROVIDER", "mock")

    payload = prefs.model_dump(exclude_none=True)

    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "recommendations" in data
    assert "summary" in data
    assert "relaxed_constraints" in data
    assert "total_matches" in data

    recs = data["recommendations"]
    assert len(recs) >= 1
    assert recs[0]["rank"] == 1
    assert recs[0]["restaurant"]["id"] == r1.id
    assert "explanation" in recs[0]


def test_recommendations_integration_constraint_relaxation(monkeypatch):
    """
    Tests full pipeline when constraints are overly strict and require relaxation.
    """
    async def mock_generate_completion(self, sys_prompt, user_prompt):
        return "{}"

    from src.llm.client import MockLLMClient
    monkeypatch.setattr(MockLLMClient, "generate_completion", mock_generate_completion)
    monkeypatch.setattr("src.config.settings.LLM_PROVIDER", "mock")

    repo = get_repository()
    cities = repo.get_cities()
    target_city = cities[0]

    payload = {
        "city": target_city,
        "location": "NonExistentLocation123",
        "cuisines": ["NonExistentCuisine999"],
        "budget": "low",
        "min_rating": 4.9,
        "top_k": 3
    }

    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200

    data = response.json()
    # Check that constraints were relaxed
    assert len(data["relaxed_constraints"]) > 0
    # Rule fallback or relaxed matches returned
    assert "recommendations" in data


def test_recommendations_invalid_city_error():
    """
    Verifies 400 Bad Request error when an unknown city is requested.
    """
    payload = {
        "city": "UnknownCityXYZ",
        "top_k": 5
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 400
    assert "Unknown city" in response.json()["detail"]
