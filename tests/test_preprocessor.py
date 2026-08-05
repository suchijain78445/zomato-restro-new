import pandas as pd

from src.data.preprocessor import (
    assign_budget_tier,
    generate_restaurant_id,
    parse_boolean,
    parse_cost,
    parse_cuisines,
    parse_dishes,
    parse_rating,
    preprocess_dataframe,
)


def test_parse_rating_valid():
    assert parse_rating("4.1/5") == 4.1
    assert parse_rating(" 4.1 /5 ") == 4.1
    assert parse_rating("3.5") == 3.5
    assert parse_rating("5.0/5") == 5.0
    assert parse_rating("0.0/5") == 0.0


def test_parse_rating_edge_cases():
    assert parse_rating("NEW") is None
    assert parse_rating("-") is None
    assert parse_rating("") is None
    assert parse_rating(None) is None
    assert parse_rating("good") is None
    assert parse_rating("N/A") is None


def test_parse_rating_clamping():
    assert parse_rating("6.2/5") == 5.0
    assert parse_rating("-1.5/5") == 0.0


def test_parse_cost_valid():
    assert parse_cost("1,200") == 1200
    assert parse_cost("300") == 300
    assert parse_cost(500) == 500
    assert parse_cost(" 1500 ") == 1500


def test_parse_cost_edge_cases():
    assert parse_cost("-") is None
    assert parse_cost("for two") is None
    assert parse_cost("") is None
    assert parse_cost(None) is None
    assert parse_cost("0") is None
    assert parse_cost("-100") is None


def test_assign_budget_tier():
    assert assign_budget_tier(300) == "low"
    assert assign_budget_tier(500) == "low"
    assert assign_budget_tier(501) == "medium"
    assert assign_budget_tier(1200) == "medium"
    assert assign_budget_tier(1500) == "medium"
    assert assign_budget_tier(1501) == "high"
    assert assign_budget_tier(2500) == "high"
    assert assign_budget_tier(None) is None
    assert assign_budget_tier(-50) is None


def test_parse_cuisines():
    assert parse_cuisines("North Indian, Chinese, Mughlai") == [
        "north indian",
        "chinese",
        "mughlai",
    ]
    assert parse_cuisines("North Indian , Chinese ") == ["north indian", "chinese"]
    assert parse_cuisines("Chinese, chinese, Chinese") == ["chinese"]
    assert parse_cuisines("") == []
    assert parse_cuisines(None) == []


def test_parse_boolean():
    assert parse_boolean("Yes") is True
    assert parse_boolean("yes") is True
    assert parse_boolean("True") is True
    assert parse_boolean(True) is True
    assert parse_boolean("No") is False
    assert parse_boolean("no") is False
    assert parse_boolean(None) is False


def test_parse_dishes():
    assert parse_dishes("Pasta, Pizza, Salad") == ["Pasta", "Pizza", "Salad"]
    assert parse_dishes(" Pasta , ") == ["Pasta"]
    assert parse_dishes(None) == []


def test_generate_restaurant_id():
    id1 = generate_restaurant_id("Jalsa", "Banashankari, Bangalore")
    id2 = generate_restaurant_id("jalsa ", " banashankari, bangalore")
    id3 = generate_restaurant_id("Jalsa", "Indiranagar, Bangalore")

    assert id1 == id2  # Case & whitespace insensitive
    assert id1 != id3  # Different addresses produce different IDs


def test_preprocess_dataframe():
    raw_data = {
        "name": ["Jalsa", "Jalsa", "Spicy Bite", None],
        "listed_in(city)": ["Bangalore", "Bangalore", "Bangalore", "Delhi"],
        "location": ["Banashankari", "Banashankari", "BTM", "Connaught Place"],
        "cuisines": [
            "North Indian, Moghlai",
            "North Indian, Moghlai",
            "Chinese",
            "South Indian",
        ],
        "rate": ["4.1/5", "4.1/5", "NEW", "3.8/5"],
        "approx_cost(for two people)": ["800", "800", "300", "1,600"],
        "rest_type": ["Casual Dining", "Casual Dining", "Quick Bites", "Cafe"],
        "votes": [775, 775, 10, 50],
        "online_order": ["Yes", "Yes", "No", "Yes"],
        "book_table": ["Yes", "Yes", "No", "No"],
        "address": [
            "Banashankari 2nd Stage",
            "Banashankari 2nd Stage",
            "BTM Layout",
            "CP",
        ],
        "dish_liked": [
            "Pasta, Mocktails",
            "Pasta, Mocktails",
            None,
            "Filter Coffee",
        ],
    }

    df_raw = pd.DataFrame(raw_data)
    processed = preprocess_dataframe(df_raw)

    # 1 row dropped (missing name), 1 duplicate dropped -> 2 rows remain
    assert len(processed) == 2
    assert set(processed["name"]) == {"Jalsa", "Spicy Bite"}
    assert processed.iloc[0]["rating"] == 4.1
    assert processed.iloc[0]["budget_tier"] == "medium"
    assert pd.isna(processed.iloc[1]["rating"])
    assert processed.iloc[1]["budget_tier"] == "low"

