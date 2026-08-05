from typing import Literal, Optional

from pydantic import BaseModel, Field


class Restaurant(BaseModel):
    """
    Normalized domain model for a restaurant.
    """

    id: str = Field(
        ..., description="Unique deterministic hash based on name and address"
    )
    name: str = Field(..., description="Name of the restaurant")
    city: str = Field(..., description="City or top-level area listed in Zomato")
    location: str = Field(..., description="Specific neighborhood or location")
    cuisines: list[str] = Field(
        default_factory=list,
        description="List of cuisines normalized to lowercase",
    )
    rating: Optional[float] = Field(
        None, description="Parsed numeric rating out of 5.0"
    )
    cost_for_two: Optional[int] = Field(
        None, description="Approximate cost for two people in INR"
    )
    budget_tier: Optional[Literal["low", "medium", "high"]] = Field(
        None, description="Budget classification"
    )
    restaurant_type: Optional[str] = Field(
        None, description="Type of restaurant (e.g., Casual Dining, Cafe)"
    )
    votes: int = Field(0, description="Total user votes")
    online_order: bool = Field(
        False, description="Whether online ordering is available"
    )
    book_table: bool = Field(
        False, description="Whether table booking is available"
    )
    address: str = Field("", description="Full address of the restaurant")
    url: Optional[str] = Field(None, description="Zomato listing URL")
    popular_dishes: list[str] = Field(
        default_factory=list,
        description="List of popular dishes liked by customers",
    )
