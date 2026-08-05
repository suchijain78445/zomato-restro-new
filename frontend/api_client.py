import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Exception raised when API communication fails."""

    pass


class APIClient:
    """
    HTTP client helper for interacting with the FastAPI backend service.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        if base_url is None:
            base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get_client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def get_cities(self) -> List[str]:
        """Fetch list of available cities from GET /metadata/cities."""
        try:
            with self._get_client() as client:
                res = client.get("/metadata/cities")
                res.raise_for_status()
                return res.json().get("cities", [])
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Failed to fetch cities: {e}")
            raise APIClientError(f"Failed to connect to backend server: {e}")

    def get_locations(self, city: Optional[str] = None) -> List[str]:
        """Fetch locations filtered by city from GET /metadata/locations."""
        try:
            params = {"city": city} if city else {}
            with self._get_client() as client:
                res = client.get("/metadata/locations", params=params)
                res.raise_for_status()
                return res.json().get("locations", [])
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Failed to fetch locations for city '{city}': {e}")
            return []

    def get_cuisines(self) -> List[str]:
        """Fetch list of all available cuisines from GET /metadata/cuisines."""
        try:
            with self._get_client() as client:
                res = client.get("/metadata/cuisines")
                res.raise_for_status()
                return res.json().get("cuisines", [])
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Failed to fetch cuisines: {e}")
            return []

    def get_recommendations(
        self, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send user preferences to POST /recommendations."""
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
        except httpx.RequestError as e:
            logger.error(f"Network error during recommendations call: {e}")
            raise APIClientError(
                "Unable to reach recommendation backend API. "
                "Please ensure FastAPI server is running."
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during recommendations call: {e}")
            raise APIClientError(
                f"Backend API error: {e.response.status_code}"
            )
