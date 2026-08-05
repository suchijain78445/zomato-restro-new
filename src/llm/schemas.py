from typing import Optional

from pydantic import BaseModel, Field


class RankedRecommendationItem(BaseModel):
    """
    Individual restaurant recommendation item produced by the LLM.
    """

    restaurant_id: str = Field(
        ..., description="Unique ID matching one of the candidate restaurants"
    )
    rank: int = Field(..., ge=1, description="1-indexed recommendation rank")
    explanation: str = Field(
        ...,
        description=(
            "Natural language explanation detailing why this restaurant matches "
            "the user's preferences and dietary notes"
        ),
    )


class LLMRankingResponse(BaseModel):
    """
    Structured JSON response output expected from the LLM.
    """

    recommendations: list[RankedRecommendationItem] = Field(
        ..., description="Ranked list of recommendations produced by LLM"
    )
    summary: Optional[str] = Field(
        None, description="Overview summary of recommended choices"
    )
