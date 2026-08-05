import json
from typing import Any, Dict, List

from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant


class PromptBuilder:
    """
    Constructs structured system and user prompts for LLM ranking.
    """

    SYSTEM_PROMPT = (
        "You are an expert restaurant recommendation engine and food critic.\n"
        "Your task is to review a pre-filtered list of candidate restaurants\n"
        "and select and rank the best recommendations matching the user's\n"
        "explicit preferences and any special notes or dietary requirements.\n\n"
        "STRICT CONSTRAINTS:\n"
        "1. You MUST ONLY recommend restaurants from the provided candidates list.\n"
        "2. You MUST use the exact 'id' string as 'restaurant_id'.\n"
        "3. DO NOT invent or hallucinate any non-existent restaurants.\n"
        "4. Your output MUST be a valid JSON object matching the required schema.\n\n"
        "REQUIRED JSON OUTPUT SCHEMA:\n"
        "{\n"
        '  "recommendations": [\n'
        "    {\n"
        '      "restaurant_id": "<exact_candidate_id>",\n'
        '      "rank": 1,\n'
        '      "explanation": "<2-3 sentence personalized reasoning>"\n'
        "    }\n"
        "  ],\n"
        '  "summary": "<1-2 sentence overview of the recommended options>"\n'
        "}"
    )

    def build_system_prompt(self) -> str:
        """Returns the static system prompt instructions."""
        return self.SYSTEM_PROMPT

    def build_user_prompt(
        self, prefs: UserPreferences, candidates: List[Restaurant]
    ) -> str:
        """
        Builds the user prompt containing user preferences and compact candidate JSON.
        """
        user_pref_dict: Dict[str, Any] = {
            "city": prefs.city,
            "location": prefs.location,
            "budget_tier": prefs.budget,
            "preferred_cuisines": prefs.cuisines,
            "minimum_rating": prefs.min_rating,
            "online_order_required": prefs.online_order,
            "book_table_required": prefs.book_table,
            "additional_notes": prefs.additional_notes,
            "requested_count": prefs.top_k,
        }

        compact_candidates = []
        for r in candidates:
            compact_candidates.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "location": r.location,
                    "cuisines": r.cuisines,
                    "rating": r.rating,
                    "cost_for_two": r.cost_for_two,
                    "budget_tier": r.budget_tier,
                    "votes": r.votes,
                    "popular_dishes": r.popular_dishes[:5],
                }
            )

        payload = {
            "user_preferences": user_pref_dict,
            "candidate_restaurants": compact_candidates,
        }

        return (
            "Below are the user preferences and candidate restaurants. "
            "Please analyze the candidates and return top recommendations "
            "in the required JSON schema:\n\n"
            f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
        )
