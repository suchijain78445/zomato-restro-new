import sys
import os

# Prevent uvicorn/fastapi from loading (causes GZipResponder crash on Streamlit Cloud)
sys.modules['uvicorn'] = None
sys.modules['fastapi'] = None

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Exception raised when API communication fails."""

    pass


def _run_coroutine_sync(coro):
    """Safely runs an async coroutine in synchronous contexts."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


class APIClient:
    """
    Client helper supporting both HTTP API calls to FastAPI backend
    and direct in-memory Python service execution for standalone Streamlit deployment.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        force_direct: bool = False,
    ):
        if base_url is None:
            base_url = os.getenv("API_BASE_URL", "")

        self.base_url = base_url.rstrip("/") if base_url else ""
        self.timeout = timeout
        self.force_direct = force_direct or (
            os.getenv("USE_DIRECT_MODE", "").lower() in ("true", "1")
        )
        self._mode = (
            "direct" if (self.force_direct or not self.base_url) else "http"
        )
        self._repo = None
        self._rec_service = None

    @property
    def mode(self) -> str:
        return self._mode

    def _get_direct_services(self):
        if self._repo is None:
            try:
                from src.data.repository import RestaurantRepository
                from src.services.recommendation_service import RecommendationService

                self._repo = RestaurantRepository()
                self._rec_service = RecommendationService(self._repo)
            except Exception as e:
                logger.error(f"Failed to load backend services: {e}")
                self._repo = None
                self._rec_service = None
        return self._repo, self._rec_service

    def _get_client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def get_cities(self) -> List[str]:
        """Fetch list of available cities."""
        if self._mode == "http":
            try:
                with self._get_client() as client:
                    res = client.get("/metadata/cities")
                    res.raise_for_status()
                    return res.json().get("cities", [])
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(
                    f"HTTP backend connection to '{self.base_url}' failed: {e}. "
                    "Switching to direct in-memory service mode."
                )
                self._mode = "direct"

        # Direct in-memory mode
        repo, _ = self._get_direct_services()
        return repo.get_cities()

    def get_locations(self, city: Optional[str] = None) -> List[str]:
        """Fetch locations filtered by city."""
        if self._mode == "http":
            try:
                params = {"city": city} if city else {}
                with self._get_client() as client:
                    res = client.get("/metadata/locations", params=params)
                    res.raise_for_status()
                    return res.json().get("locations", [])
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(
                    f"HTTP locations lookup failed: {e}. Falling back to direct mode."
                )
                self._mode = "direct"

        repo, _ = self._get_direct_services()
        return repo.get_locations(city)

    def get_cuisines(self) -> List[str]:
        """Fetch list of all available cuisines."""
        if self._mode == "http":
            try:
                with self._get_client() as client:
                    res = client.get("/metadata/cuisines")
                    res.raise_for_status()
                    return res.json().get("cuisines", [])
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(
                    f"HTTP cuisines lookup failed: {e}. Falling back to direct mode."
                )
                self._mode = "direct"

        repo, _ = self._get_direct_services()
        return repo.get_cuisines()

    def get_recommendations(
        self, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send user preferences for recommendations."""
        if self._mode == "http":
            try:
                with self._get_client() as client:
                    res = client.post("/recommendations", json=preferences)
                    if res.status_code == 400:
                        detail = res.json().get(
                            "detail", "Invalid request parameters."
                        )
                        raise APIClientError(detail)
                    elif res.status_code == 422:
                        raise APIClientError(
                            "Validation error in request parameters."
                        )
                    res.raise_for_status()
                    return res.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if isinstance(e, APIClientError):
                    raise
                logger.warning(
                    f"HTTP recommendations call failed ({e}). Falling back to direct mode."
                )
                self._mode = "direct"

        # Direct in-memory mode execution
        try:
            from pydantic import ValidationError
            from src.models.preferences import UserPreferences

            repo, rec_service = self._get_direct_services()

            # Validate requested city against dataset metadata
            available_cities = repo.get_cities()
            req_city = preferences.get("city", "")
            city_matched = any(
                c.strip().lower() == str(req_city).strip().lower()
                for c in available_cities
            )

            if not city_matched:
                raise APIClientError(
                    f"Unknown city '{req_city}'. Available cities are: "
                    f"{', '.join(available_cities)}"
                )

            user_prefs = UserPreferences(**preferences)
            response = _run_coroutine_sync(
                rec_service.get_recommendations(user_prefs)
            )
            return response.model_dump()
        except ValidationError as ve:
            raise APIClientError(f"Validation error in request parameters: {ve}")
        except APIClientError:
            raise
        except Exception as e:
            logger.error(
                f"Error executing recommendation in direct mode: {e}", exc_info=True
            )
            raise APIClientError(f"Recommendation engine error: {str(e)}")
