import json

import pytest

from src.data.repository import RestaurantRepository
from src.llm.client import MockLLMClient
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.recommendation_service import RecommendationService


@pytest.fixture
def mock_repository(tmp_path):
    repo = RestaurantRepository(
        parquet_path=str(tmp_path / "test.parquet"),
        metadata_dir=str(tmp_path / "metadata"),
        auto_load=False,
    )

    r1 = Restaurant(
        id="r1",
        name="Jalsa",
        city="Bangalore",
        location="Banashankari",
        cuisines=["north indian"],
        rating=4.1,
        cost_for_two=800,
        budget_tier="medium",
        votes=500,
        address="Banashankari, Bangalore",
    )
    r2 = Restaurant(
        id="r2",
        name="Spice Elephant",
        city="Bangalore",
        location="Banashankari",
        cuisines=["chinese"],
        rating=4.5,
        cost_for_two=400,
        budget_tier="low",
        votes=1000,
        address="Banashankari 2nd Stage",
    )

    repo._restaurants = [r1, r2]
    repo._id_index = {"r1": r1, "r2": r2}
    repo._cities = ["Bangalore"]
    return repo


@pytest.mark.anyio
async def test_recommendation_service_with_mock_llm(mock_repository):
    mock_response = json.dumps(
        {
            "recommendations": [
                {
                    "restaurant_id": "r1",
                    "rank": 1,
                    "explanation": "AI generated explanation for Jalsa",
                }
            ],
            "summary": "AI summary of top picks",
        }
    )

    mock_llm = MockLLMClient(default_response=mock_response)
    service = RecommendationService(mock_repository, llm_client=mock_llm)

    prefs = UserPreferences(city="Bangalore", top_k=2)
    res = await service.get_recommendations(prefs)

    assert len(res.recommendations) == 1
    assert res.recommendations[0].restaurant.id == "r1"
    assert res.recommendations[0].explanation == "AI generated explanation for Jalsa"
    assert res.summary == "AI summary of top picks"


@pytest.mark.anyio
async def test_recommendation_service_hallucination_guard(mock_repository):
    # LLM returns a hallucinated ID "r999" not in candidates
    mock_response = json.dumps(
        {
            "recommendations": [
                {
                    "restaurant_id": "r999",
                    "rank": 1,
                    "explanation": "Fake restaurant explanation",
                }
            ],
            "summary": "Fake summary",
        }
    )

    mock_llm = MockLLMClient(default_response=mock_response)
    service = RecommendationService(mock_repository, llm_client=mock_llm)

    prefs = UserPreferences(city="Bangalore", top_k=2)
    res = await service.get_recommendations(prefs)

    # Hallucinated ID is filtered out -> falls back to rule-based ranking
    assert len(res.recommendations) == 2
    assert res.recommendations[0].restaurant.id in ("r1", "r2")
    assert "Rule-based recommendation:" in res.summary


@pytest.mark.anyio
async def test_recommendation_service_fallback_on_error(mock_repository):
    # LLM returns invalid JSON
    mock_llm = MockLLMClient(default_response="INVALID JSON STRING")
    service = RecommendationService(mock_repository, llm_client=mock_llm)

    prefs = UserPreferences(city="Bangalore", top_k=2)
    res = await service.get_recommendations(prefs)

    # Falls back gracefully to rule-based recommendations
    assert len(res.recommendations) == 2
    assert "Rule-based recommendation:" in res.summary


def test_get_llm_client_groq_factory(monkeypatch):
    from src.config import get_settings
    from src.llm.client import GroqClient, get_llm_client

    settings = get_settings()
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    client = get_llm_client()
    assert isinstance(client, GroqClient)

