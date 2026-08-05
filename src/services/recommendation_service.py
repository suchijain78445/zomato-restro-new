import json
import logging
import re
import time
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError

from src.config import settings
from src.data.repository import RestaurantRepository
from src.llm.client import LLMClient, get_llm_client
from src.llm.schemas import LLMRankingResponse
from src.models.preferences import UserPreferences
from src.models.recommendation import RecommendationItem, RecommendationResponse
from src.models.restaurant import Restaurant
from src.services.filter_service import FilterService
from src.services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


def clean_json_response(raw_text: str) -> str:
    """
    Strips markdown code fences (e.g., ```json ... ```) from raw text.
    """
    text = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


class RecommendationService:
    """
    Orchestrates candidate filtering, LLM prompt construction,
    completion generation, response parsing, hallucination guarding, and fallback.
    """

    def __init__(
        self,
        repository: RestaurantRepository,
        llm_client: Optional[LLMClient] = None,
        filter_service: Optional[FilterService] = None,
        prompt_builder: Optional[PromptBuilder] = None,
    ):
        self.repository = repository
        self.llm_client = llm_client or get_llm_client()
        self.filter_service = filter_service or FilterService(repository)
        self.prompt_builder = prompt_builder or PromptBuilder()

    async def get_recommendations(
        self, prefs: UserPreferences
    ) -> RecommendationResponse:
        """
        Main entrypoint for generating restaurant recommendations.
        """
        start_time = time.perf_counter()
        logger.info(
            f"Processing recommendation request for city='{prefs.city}', "
            f"location='{prefs.location}', cuisines='{prefs.cuisines}', "
            f"budget='{prefs.budget}', min_rating={prefs.min_rating}"
        )

        # Step 1: Filter candidates using FilterService
        candidates, relaxed_constraints, total_matches = (
            self.filter_service.filter_restaurants(
                prefs, max_candidates=settings.MAX_CANDIDATES_FOR_LLM
            )
        )
        logger.info(
            f"FilterService returned {len(candidates)} candidates "
            f"(total_matches={total_matches}, relaxed_constraints={relaxed_constraints})"
        )

        if not candidates:
            logger.info("No candidates found after filtering & relaxation.")
            return RecommendationResponse(
                recommendations=[],
                summary=f"No restaurants found matching your criteria in {prefs.city}.",
                relaxed_constraints=relaxed_constraints,
                total_matches=0,
            )

        # Candidate lookup map for validation & hallucination guard
        candidate_map: Dict[str, Restaurant] = {r.id: r for r in candidates}

        # Step 2: Attempt LLM-based ranking
        recommendations, llm_summary = await self._attempt_llm_ranking(
            prefs, candidates, candidate_map
        )

        # Step 3: Fallback to rule-based ranking if LLM returned 0 items
        if not recommendations:
            logger.info(
                "LLM path unavailable or returned 0 items. Using rule-based fallback."
            )
            recommendations = self._rule_based_fallback(candidates, prefs.top_k)
            summary = self._build_summary(
                prefs.city, total_matches, relaxed_constraints, is_fallback=True
            )
        else:
            summary = (
                llm_summary
                or self._build_summary(
                    prefs.city, total_matches, relaxed_constraints, is_fallback=False
                )
            )

        elapsed = time.perf_counter() - start_time
        logger.info(
            f"Completed recommendation request in {elapsed:.3f}s. "
            f"Returned {len(recommendations)} recommendations."
        )

        return RecommendationResponse(
            recommendations=recommendations,
            summary=summary,
            relaxed_constraints=relaxed_constraints,
            total_matches=total_matches,
        )

    async def _attempt_llm_ranking(
        self,
        prefs: UserPreferences,
        candidates: List[Restaurant],
        candidate_map: Dict[str, Restaurant],
    ) -> Tuple[List[RecommendationItem], Optional[str]]:
        """
        Attempts LLM completion generation with 1 retry on JSON parse failure.
        Applies hallucination guard and measures latency.
        """
        sys_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(prefs, candidates)

        for attempt in range(2):
            llm_start = time.perf_counter()
            try:
                raw_response = await self.llm_client.generate_completion(
                    sys_prompt, user_prompt
                )
                llm_latency = time.perf_counter() - llm_start
                logger.info(
                    f"LLM call attempt {attempt + 1} completed in {llm_latency:.3f}s."
                )

                cleaned_json = clean_json_response(raw_response)
                parsed_data = json.loads(cleaned_json)
                llm_resp = LLMRankingResponse(**parsed_data)

                # Hallucination Guard: keep only items whose ID exists in candidate_map
                valid_items: List[RecommendationItem] = []
                seen_ids = set()

                for item in llm_resp.recommendations:
                    rid = item.restaurant_id
                    if rid in candidate_map and rid not in seen_ids:
                        seen_ids.add(rid)
                        rest_obj = candidate_map[rid]
                        valid_items.append(
                            RecommendationItem(
                                restaurant=rest_obj,
                                rank=len(valid_items) + 1,
                                explanation=item.explanation,
                            )
                        )
                        if len(valid_items) >= prefs.top_k:
                            break

                if valid_items:
                    logger.info(
                        f"LLM ranking successful on attempt {attempt + 1}: "
                        f"{len(valid_items)} valid recommendations parsed."
                    )
                    return valid_items, llm_resp.summary
                else:
                    logger.warning(
                        f"Attempt {attempt + 1}: LLM response had no valid IDs matching candidates."
                    )

            except (json.JSONDecodeError, ValidationError, Exception) as e:
                llm_latency = time.perf_counter() - llm_start
                logger.warning(
                    f"Attempt {attempt + 1} failed after {llm_latency:.3f}s during LLM invocation: {e}"
                )

        return [], None

    def _rule_based_fallback(
        self, candidates: List[Restaurant], top_k: int
    ) -> List[RecommendationItem]:
        """
        Produces top_k rule-based recommendations as fallback.
        """
        items = []
        for idx, rest in enumerate(candidates[:top_k], start=1):
            rating_str = (
                f"{rest.rating}/5.0" if rest.rating is not None else "Unrated"
            )
            explanation = (
                f"Rated {rating_str} with {rest.votes} votes in {rest.location}. "
                f"Cost for two: ₹{rest.cost_for_two or 'N/A'} "
                f"({rest.budget_tier or 'N/A'} budget)."
            )
            items.append(
                RecommendationItem(
                    restaurant=rest,
                    rank=idx,
                    explanation=explanation,
                )
            )
        return items

    def _build_summary(
        self,
        city: str,
        total_matches: int,
        relaxed_constraints: List[str],
        is_fallback: bool,
    ) -> str:
        prefix = "Rule-based recommendation: " if is_fallback else ""
        if relaxed_constraints:
            relaxed_str = ", ".join(relaxed_constraints)
            return (
                f"{prefix}Found {total_matches} matching restaurants in {city} "
                f"after relaxing constraint(s): {relaxed_str}."
            )
        return f"{prefix}Found {total_matches} matching restaurants in {city}."
