from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.prompt_builder import PromptBuilder


def test_build_system_prompt():
    builder = PromptBuilder()
    sys_prompt = builder.build_system_prompt()
    assert "STRICT CONSTRAINTS" in sys_prompt
    assert "restaurant_id" in sys_prompt


def test_build_user_prompt():
    builder = PromptBuilder()
    prefs = UserPreferences(
        city="Bangalore",
        location="Banashankari",
        budget="medium",
        cuisines=["north indian"],
        additional_notes="Prefer outdoor seating",
    )
    r1 = Restaurant(
        id="hash_123",
        name="Jalsa",
        city="Bangalore",
        location="Banashankari",
        cuisines=["north indian", "mughlai"],
        rating=4.1,
        cost_for_two=800,
        budget_tier="medium",
        address="Banashankari, Bangalore",
    )

    user_prompt = builder.build_user_prompt(prefs, [r1])
    assert "Bangalore" in user_prompt
    assert "Prefer outdoor seating" in user_prompt
    assert "hash_123" in user_prompt
    assert "Jalsa" in user_prompt
