import pytest

from src.data.repository import RestaurantRepository
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.filter_service import FilterService


@pytest.fixture
def mock_repository(tmp_path):
    repo = RestaurantRepository(
        parquet_path=str(tmp_path / "test.parquet"),
        metadata_dir=str(tmp_path / "metadata"),
        auto_load=False,
    )

    restaurants = [
        Restaurant(
            id="r1",
            name="Jalsa",
            city="Bangalore",
            location="Banashankari",
            cuisines=["north indian", "mughlai"],
            rating=4.1,
            cost_for_two=800,
            budget_tier="medium",
            votes=775,
            online_order=True,
            book_table=True,
            address="Banashankari, Bangalore",
        ),
        Restaurant(
            id="r2",
            name="Spice Elephant",
            city="Bangalore",
            location="Banashankari",
            cuisines=["chinese", "thai"],
            rating=4.5,
            cost_for_two=400,
            budget_tier="low",
            votes=1200,
            online_order=True,
            book_table=False,
            address="Banashankari 2nd Stage",
        ),
        Restaurant(
            id="r3",
            name="San Churro Cafe",
            city="Bangalore",
            location="Banashankari",
            cuisines=["cafe", "italian"],
            rating=3.8,
            cost_for_two=1400,
            budget_tier="medium",
            votes=300,
            online_order=False,
            book_table=False,
            address="Banashankari 3rd Stage",
        ),
        Restaurant(
            id="r4",
            name="Truffles",
            city="Bangalore",
            location="Koramangala",
            cuisines=["american", "burger", "cafe"],
            rating=4.7,
            cost_for_two=900,
            budget_tier="medium",
            votes=5000,
            online_order=True,
            book_table=True,
            address="Koramangala, Bangalore",
        ),
        Restaurant(
            id="r5",
            name="New Food Corner",
            city="Bangalore",
            location="Banashankari",
            cuisines=["north indian"],
            rating=None,
            cost_for_two=300,
            budget_tier="low",
            votes=20,
            online_order=False,
            book_table=False,
            address="Banashankari Main",
        ),
        Restaurant(
            id="r6",
            name="Karim's",
            city="Delhi",
            location="Chandni Chowk",
            cuisines=["mughlai"],
            rating=4.6,
            cost_for_two=1200,
            budget_tier="medium",
            votes=3000,
            address="Chandni Chowk, Delhi",
        ),
    ]

    repo._restaurants = restaurants
    repo._id_index = {r.id: r for r in restaurants}
    repo._cities = ["Bangalore", "Delhi"]
    return repo


def test_filter_exact_match(mock_repository):
    service = FilterService(mock_repository)
    prefs = UserPreferences(
        city="Bangalore",
        location="Banashankari",
        budget="medium",
        cuisines=["north indian"],
    )
    candidates, relaxed, total = service.filter_restaurants(prefs)

    # 1 exact match (Jalsa: r1)
    # But candidates count is 1 (< 5), so constraint relaxation is triggered.
    # Relaxation cascade: location -> cuisines -> budget -> min_rating
    # Step 1: relax location -> matches (r1..r6) filtered by budget
    #         medium + cuisine north indian -> r1
    # Step 2: relax cuisines -> budget medium in Bangalore: r1, r3, r4 (3 items)
    # Step 3: relax budget -> all items in Bangalore: r1, r2, r3, r4, r5 (5 items!)
    assert len(candidates) == 5
    assert "location" in relaxed
    assert "cuisines" in relaxed
    assert "budget" in relaxed


def test_filter_without_relaxation(mock_repository):
    service = FilterService(mock_repository)
    # Search for all restaurants in Bangalore without restrictive location/budget
    prefs = UserPreferences(city="Bangalore")
    candidates, relaxed, total = service.filter_restaurants(prefs)

    assert len(candidates) == 5
    assert len(relaxed) == 0
    # Top item should be Truffles (rating 4.7)
    assert candidates[0].name == "Truffles"
    # Unrated item (New Food Corner) should be sorted last
    assert candidates[-1].name == "New Food Corner"


def test_filter_min_rating(mock_repository):
    service = FilterService(mock_repository)
    prefs = UserPreferences(city="Bangalore", min_rating=4.0)
    candidates, relaxed, total = service.filter_restaurants(prefs)

    # Ratings >= 4.0 in Bangalore:
    # Truffles (4.7), Spice Elephant (4.5), Jalsa (4.1) -> 3 items
    # Since 3 < 5, min_rating is relaxed as last resort
    assert len(candidates) == 5
    assert "min_rating" in relaxed


def test_sorting_order(mock_repository):
    service = FilterService(mock_repository)
    prefs = UserPreferences(city="Bangalore")
    candidates, _, _ = service.filter_restaurants(prefs)

    # Expect: Truffles (4.7), Spice Elephant (4.5), Jalsa (4.1),
    # San Churro (3.8), New Food Corner (None)
    ratings = [c.rating for c in candidates]
    assert ratings == [4.7, 4.5, 4.1, 3.8, None]

