import pytest
from fastapi.testclient import TestClient

from src.api.routes.metadata import get_repository
from src.data.repository import RestaurantRepository
from src.main import app
from src.models.restaurant import Restaurant


@pytest.fixture
def mock_repository(tmp_path):
    repo = RestaurantRepository(
        parquet_path=str(tmp_path / "test.parquet"),
        metadata_dir=str(tmp_path / "metadata"),
        auto_load=False,
    )

    r1 = Restaurant(
        id="hash1",
        name="Jalsa",
        city="Bangalore",
        location="Banashankari",
        cuisines=["north indian", "chinese"],
        rating=4.1,
        cost_for_two=800,
        budget_tier="medium",
        votes=500,
        address="Banashankari, Bangalore",
    )
    r2 = Restaurant(
        id="hash2",
        name="Karim's",
        city="Delhi",
        location="Chandni Chowk",
        cuisines=["mughlai"],
        rating=4.5,
        cost_for_two=1200,
        budget_tier="medium",
        votes=1000,
        address="Chandni Chowk, Delhi",
    )

    repo._restaurants = [r1, r2]
    repo._id_index = {r1.id: r1, r2.id: r2}
    repo._cities = ["Bangalore", "Delhi"]
    return repo


@pytest.fixture
def client(mock_repository):
    app.dependency_overrides[get_repository] = lambda: mock_repository
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_post_recommendations_success(client):
    payload = {
        "city": "Bangalore",
        "location": "Banashankari",
        "budget": "medium",
        "cuisines": ["north indian"],
        "min_rating": 4.0,
        "top_k": 2,
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) == 1
    assert data["recommendations"][0]["restaurant"]["name"] == "Jalsa"
    assert data["recommendations"][0]["rank"] == 1
    assert "summary" in data


def test_post_recommendations_unknown_city(client):
    payload = {
        "city": "NonExistentCity",
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 400
    assert "Unknown city 'NonExistentCity'" in response.json()["detail"]


def test_post_recommendations_invalid_rating(client):
    payload = {
        "city": "Bangalore",
        "min_rating": 6.5,
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 422


def test_post_recommendations_notes_too_long(client):
    payload = {
        "city": "Bangalore",
        "additional_notes": "A" * 501,
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 422
