from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class UserPreferences(BaseModel):
    """
    Request model for user restaurant preferences.
    """

    city: str = Field(..., description="Target city for restaurant search")
    location: Optional[str] = Field(
        None, description="Specific neighborhood or area in the city"
    )
    budget: Optional[Literal["low", "medium", "high"]] = Field(
        None, description="Budget classification ('low', 'medium', 'high')"
    )
    cuisines: list[str] = Field(
        default_factory=list,
        description="List of preferred cuisine tags",
    )
    min_rating: Optional[float] = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Minimum acceptable rating out of 5.0",
    )
    online_order: Optional[bool] = Field(
        None, description="Require online ordering availability"
    )
    book_table: Optional[bool] = Field(
        None, description="Require table booking availability"
    )
    additional_notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Free-text preferences for LLM ranking",
    )
    top_k: int = Field(
        5,
        ge=1,
        le=25,
        description="Number of recommendations to return",
    )

    @field_validator("city")
    @classmethod
    def validate_city_not_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("City cannot be empty or whitespace")
        return s
