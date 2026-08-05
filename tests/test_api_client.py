from frontend.api_client import APIClient, APIClientError


def test_api_client_direct_mode():
    client = APIClient(force_direct=True)
    assert client.mode == "direct"

    cities = client.get_cities()
    assert isinstance(cities, list)
    assert len(cities) > 0

    locations = client.get_locations(cities[0])
    assert isinstance(locations, list)

    cuisines = client.get_cuisines()
    assert isinstance(cuisines, list)


def test_api_client_direct_recommendation(monkeypatch):
    from src.config import settings

    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    client = APIClient(force_direct=True)
    cities = client.get_cities()
    valid_city = cities[0]

    payload = {
        "city": valid_city,
        "top_k": 3,
    }

    res = client.get_recommendations(payload)
    assert "recommendations" in res
    assert isinstance(res["recommendations"], list)
    assert len(res["recommendations"]) <= 3



def test_api_client_invalid_city_raises_error():
    client = APIClient(force_direct=True)
    payload = {
        "city": "NonExistentCityXYZ",
        "top_k": 3,
    }
    try:
        client.get_recommendations(payload)
        assert False, "Expected APIClientError for invalid city"
    except APIClientError as e:
        assert "Unknown city" in str(e)
