import logging

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.routes.metadata import get_repository
from src.data.repository import RestaurantRepository
from src.models.preferences import UserPreferences
from src.models.recommendation import RecommendationResponse
from src.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Recommendations"])


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_recommendations(
    prefs: UserPreferences,
    repo: RestaurantRepository = Depends(get_repository),
):
    """
    Generate AI-powered restaurant recommendations based on user preferences.
    Combines deterministic filtering, prompt construction, LLM ranking,
    hallucination guarding, and fallback handling.
    """
    # 1. Validate requested city against dataset metadata
    available_cities = repo.get_cities()
    city_matched = False
    for c in available_cities:
        if c.strip().lower() == prefs.city.strip().lower():
            city_matched = True
            break

    if not city_matched:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unknown city '{prefs.city}'. Available cities are: "
                f"{', '.join(available_cities)}"
            ),
        )

    # 2. Delegate to RecommendationService orchestrator
    rec_service = RecommendationService(repo)
    return await rec_service.get_recommendations(prefs)
