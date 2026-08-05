import logging
from typing import List, Set, Tuple

from src.data.repository import RestaurantRepository
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


class FilterService:
    """
    Service responsible for deterministic restaurant filtering,
    ordered constraint relaxation, and sorting.
    """

    # Order of relaxation when fewer than 5 matching candidates are found
    RELAXATION_ORDER = ["location", "cuisines", "budget", "min_rating"]

    def __init__(self, repository: RestaurantRepository):
        self.repository = repository

    def filter_restaurants(
        self, prefs: UserPreferences, max_candidates: int = 25
    ) -> Tuple[List[Restaurant], List[str], int]:
        """
        Filters restaurants based on user preferences.
        If fewer than 5 candidates match, sequentially relaxes constraints.

        Returns:
            (candidate_restaurants, list_of_relaxed_constraints, total_matching_count)
        """
        all_restaurants = self.repository.get_all()

        # Determine initially active constraints
        active_constraints: Set[str] = set()

        if prefs.location and prefs.location.strip():
            active_constraints.add("location")
        if prefs.budget:
            active_constraints.add("budget")
        clean_cuisines = [c.strip().lower() for c in prefs.cuisines if c.strip()]
        if clean_cuisines:
            active_constraints.add("cuisines")
        if prefs.min_rating is not None:
            active_constraints.add("min_rating")
        if prefs.online_order is not None:
            active_constraints.add("online_order")
        if prefs.book_table is not None:
            active_constraints.add("book_table")

        city_target = prefs.city.strip().lower()
        relaxed_constraints: List[str] = []

        # Execute initial filter pass
        candidates = self._apply_filters(
            all_restaurants, city_target, clean_cuisines, prefs, active_constraints
        )

        # Sequential relaxation cascade if candidates < 5
        for constraint_to_relax in self.RELAXATION_ORDER:
            if len(candidates) >= 5:
                break
            if constraint_to_relax in active_constraints:
                active_constraints.remove(constraint_to_relax)
                relaxed_constraints.append(constraint_to_relax)
                logger.info(
                    f"Fewer than 5 candidates found ({len(candidates)}). "
                    f"Relaxing constraint: '{constraint_to_relax}'"
                )
                candidates = self._apply_filters(
                    all_restaurants,
                    city_target,
                    clean_cuisines,
                    prefs,
                    active_constraints,
                )

        total_matches = len(candidates)

        # Sort candidates: (rating DESC, votes DESC), with None ratings sorted last
        sorted_candidates = sorted(
            candidates,
            key=lambda r: (
                r.rating if r.rating is not None else -1.0,
                r.votes,
            ),
            reverse=True,
        )

        top_candidates = sorted_candidates[:max_candidates]
        return top_candidates, relaxed_constraints, total_matches

    def _apply_filters(
        self,
        restaurants: List[Restaurant],
        city_target: str,
        clean_cuisines: List[str],
        prefs: UserPreferences,
        active_constraints: Set[str],
    ) -> List[Restaurant]:
        """
        Applies active filtering constraints against the candidate list.
        """
        filtered = []
        loc_target = prefs.location.strip().lower() if prefs.location else ""

        for r in restaurants:
            # City filter (required hard constraint)
            if not r.city or r.city.strip().lower() != city_target:
                continue

            # Location filter
            if "location" in active_constraints and loc_target:
                if not r.location or loc_target not in r.location.strip().lower():
                    continue

            # Budget filter
            if "budget" in active_constraints:
                if r.budget_tier != prefs.budget:
                    continue

            # Cuisine filter (OR logic: match any requested cuisine)
            if "cuisines" in active_constraints and clean_cuisines:
                restaurant_cuisines = [c.lower() for c in r.cuisines]
                matched_any = any(
                    req in restaurant_cuisines
                    or any(req in rc for rc in restaurant_cuisines)
                    for req in clean_cuisines
                )
                if not matched_any:
                    continue

            # Minimum rating filter (excludes None ratings)
            if "min_rating" in active_constraints and prefs.min_rating is not None:
                if r.rating is None or r.rating < prefs.min_rating:
                    continue

            # Online order boolean filter
            if "online_order" in active_constraints:
                if r.online_order != prefs.online_order:
                    continue

            # Table booking boolean filter
            if "book_table" in active_constraints:
                if r.book_table != prefs.book_table:
                    continue

            filtered.append(r)

        return filtered
