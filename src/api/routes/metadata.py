from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.data.repository import RestaurantRepository

router = APIRouter(prefix="/metadata", tags=["Metadata"])


# Global instance or dependency injection for Repository
_repository_instance: Optional[RestaurantRepository] = None


def get_repository() -> RestaurantRepository:
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = RestaurantRepository(auto_load=True)
    return _repository_instance


@router.get("/cities", response_model=dict)
async def get_cities(repo: RestaurantRepository = Depends(get_repository)):
    """
    Get list of all available cities.
    """
    cities = repo.get_cities()
    return {"cities": cities}


@router.get("/locations", response_model=dict)
async def get_locations(
    city: Optional[str] = Query(None, description="City name to filter locations by"),
    repo: RestaurantRepository = Depends(get_repository),
):
    """
    Get list of locations/neighborhoods, optionally filtered by city.
    """
    if city is not None and not city.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="City query parameter cannot be empty",
        )

    locations = repo.get_locations(city)
    return {
        "city": city,
        "locations": locations,
    }


@router.get("/cuisines", response_model=dict)
async def get_cuisines(repo: RestaurantRepository = Depends(get_repository)):
    """
    Get list of all unique available cuisines.
    """
    cuisines = repo.get_cuisines()
    return {"cuisines": cuisines}
