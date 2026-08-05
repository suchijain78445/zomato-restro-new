from typing import Optional

from pydantic import BaseModel, Field

from src.models.restaurant import Restaurant


class RecommendationItem(BaseModel):
    """
    Individual restaurant recommendation item with rank and optional AI explanation.
    """

    restaurant: Restaurant = Field(..., description="Full restaurant domain object")
    rank: int = Field(..., ge=1, description="1-indexed recommendation rank")
    explanation: Optional[str] = Field(
        None, description="AI or rule-based reasoning for recommendation"
    )


class RecommendationResponse(BaseModel):
    """
    Response model for restaurant recommendations API.
    """

    recommendations: list[RecommendationItem] = Field(
        default_factory=list, description="Ranked list of recommended restaurants"
    )
    summary: Optional[str] = Field(
        None, description="Human-readable summary of recommendation results"
    )
    relaxed_constraints: list[str] = Field(
        default_factory=list,
        description="List of constraint names relaxed to yield sufficient results",
    )
    total_matches: int = Field(
        0, description="Total matching candidates before top_k truncation"
    )
