import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.config import settings
from src.data.loader import get_or_create_processed_data
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


class RestaurantRepository:
    """
    In-memory repository managing Restaurant domain objects and lookup indexes.
    """

    def __init__(
        self,
        parquet_path: str = settings.DATA_CACHE_PATH,
        metadata_dir: str = settings.METADATA_DIR,
        auto_load: bool = True,
    ):
        self.parquet_path = parquet_path
        self.metadata_dir = metadata_dir
        self._restaurants: List[Restaurant] = []
        self._id_index: Dict[str, Restaurant] = {}
        self._df: Optional[pd.DataFrame] = None
        self._cities: List[str] = []
        self._locations_by_city: Dict[str, List[str]] = {}
        self._cuisines: List[str] = []

        if auto_load:
            self.load()

    def load(self, force_reprocess: bool = False) -> None:
        """
        Loads the dataset into memory and builds lookup indexes.
        """
        logger.info("Initializing RestaurantRepository data...")
        self._df = get_or_create_processed_data(
            force_reprocess=force_reprocess,
            parquet_path_str=self.parquet_path,
            metadata_dir_str=self.metadata_dir,
        )

        # Convert DF rows to Restaurant Pydantic models
        records = self._df.to_dict(orient="records")
        self._restaurants = []
        self._id_index = {}

        for rec in records:
            rec_clean = {}
            for k, v in rec.items():
                if isinstance(v, (list, tuple, np.ndarray)):
                    rec_clean[k] = list(v)
                elif v is None or pd.isna(v):
                    rec_clean[k] = None
                else:
                    rec_clean[k] = v

            if not isinstance(rec_clean.get("cuisines"), list):
                rec_clean["cuisines"] = []

            if not isinstance(rec_clean.get("popular_dishes"), list):
                rec_clean["popular_dishes"] = []

            if not rec_clean.get("id"):
                rec_clean["id"] = "unknown"
            if not rec_clean.get("name"):
                rec_clean["name"] = "Unknown"
            if not rec_clean.get("city"):
                rec_clean["city"] = "Unknown"
            if not rec_clean.get("location"):
                rec_clean["location"] = "Unknown"
            if not rec_clean.get("address"):
                rec_clean["address"] = ""

            rest = Restaurant(**rec_clean)
            self._restaurants.append(rest)
            self._id_index[rest.id] = rest

        # Load or build metadata indexes
        self._load_metadata()
        logger.info(
            f"Repository loaded {len(self._restaurants)} restaurants across "
            f"{len(self._cities)} cities."
        )

    def _load_metadata(self) -> None:
        meta_path = Path(self.metadata_dir)
        cities_file = meta_path / "cities.json"
        locations_file = meta_path / "locations.json"
        cuisines_file = meta_path / "cuisines.json"

        if cities_file.exists() and locations_file.exists() and cuisines_file.exists():
            with open(cities_file, "r", encoding="utf-8") as f:
                self._cities = json.load(f)
            with open(locations_file, "r", encoding="utf-8") as f:
                self._locations_by_city = json.load(f)
            with open(cuisines_file, "r", encoding="utf-8") as f:
                self._cuisines = json.load(f)
        else:
            # Fallback: compute from memory
            self._cities = sorted(list({r.city for r in self._restaurants if r.city}))
            locations_map: Dict[str, set] = {}
            all_cuisines = set()

            for r in self._restaurants:
                if r.city:
                    if r.city not in locations_map:
                        locations_map[r.city] = set()
                    if r.location:
                        locations_map[r.city].add(r.location)
                for c in r.cuisines:
                    all_cuisines.add(c)

            self._locations_by_city = {
                city: sorted(list(locs)) for city, locs in locations_map.items()
            }
            self._cuisines = sorted(list(all_cuisines))

    def get_all(self) -> List[Restaurant]:
        """Returns all loaded restaurants."""
        return self._restaurants

    def get_by_id(self, restaurant_id: str) -> Optional[Restaurant]:
        """Looks up a restaurant by unique ID."""
        return self._id_index.get(restaurant_id)

    def get_cities(self) -> List[str]:
        """Returns unique sorted cities."""
        return self._cities

    def get_locations(self, city: Optional[str] = None) -> List[str]:
        """
        Returns locations for a given city (case-insensitive search).
        If city is None, returns all locations across all cities.
        """
        if not city:
            all_locs = set()
            for locs in self._locations_by_city.values():
                all_locs.update(locs)
            return sorted(list(all_locs))

        # Case-insensitive lookup
        city_lower = city.strip().lower()
        for c, locs in self._locations_by_city.items():
            if c.strip().lower() == city_lower:
                return locs
        return []

    def get_cuisines(self) -> List[str]:
        """Returns unique sorted cuisines."""
        return self._cuisines

    def get_dataframe(self) -> pd.DataFrame:
        """Returns the underlying pandas DataFrame."""
        if self._df is None:
            raise RuntimeError("Repository DataFrame has not been loaded.")
        return self._df
