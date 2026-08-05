import pytest
from fastapi.testclient import TestClient

from src.api.routes.metadata import get_repository
from src.data.repository import RestaurantRepository
from src.main import app
from src.models.restaurant import Restaurant


@pytest.fixture
def mock_repository(tmp_path):
    """
    Creates a mock repository loaded with test restaurants.
    """
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
        address="Banashankari, Bangalore",
    )
    r2 = Restaurant(
        id="hash2",
        name="Karim's",
        city="Delhi",
        location="Chandni Chowk",
        cuisines=["mughlai", "north indian"],
        rating=4.5,
        cost_for_two=1200,
        budget_tier="medium",
        address="Chandni Chowk, Delhi",
    )

    repo._restaurants = [r1, r2]
    repo._id_index = {r1.id: r1, r2.id: r2}
    repo._cities = ["Bangalore", "Delhi"]
    repo._locations_by_city = {
        "Bangalore": ["Banashankari"],
        "Delhi": ["Chandni Chowk"],
    }
    repo._cuisines = ["chinese", "mughlai", "north indian"]
    return repo


@pytest.fixture
def client(mock_repository):
    app.dependency_overrides[get_repository] = lambda: mock_repository
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_cities_endpoint(client):
    response = client.get("/metadata/cities")
    assert response.status_code == 200
    data = response.json()
    assert "cities" in data
    assert data["cities"] == ["Bangalore", "Delhi"]


def test_get_locations_endpoint(client):
    response = client.get("/metadata/locations?city=Bangalore")
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Bangalore"
    assert data["locations"] == ["Banashankari"]


def test_get_locations_empty_city_param(client):
    response = client.get("/metadata/locations?city=")
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_get_cuisines_endpoint(client):
    response = client.get("/metadata/cuisines")
    assert response.status_code == 200
    data = response.json()
    assert "cuisines" in data
    assert data["cuisines"] == ["chinese", "mughlai", "north indian"]
