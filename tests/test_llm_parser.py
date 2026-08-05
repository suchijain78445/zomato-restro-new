import json

from src.llm.schemas import LLMRankingResponse
from src.services.recommendation_service import clean_json_response


def test_clean_json_response_markdown():
    raw_markdown = (
        "```json\n"
        "{\n"
        '  "recommendations": [],\n'
        '  "summary": "No choices"\n'
        "}\n"
        "```"
    )
    cleaned = clean_json_response(raw_markdown)
    assert cleaned.startswith("{")
    assert cleaned.endswith("}")
    data = json.loads(cleaned)
    assert data["summary"] == "No choices"


def test_llm_ranking_response_schema():
    payload = {
        "recommendations": [
            {
                "restaurant_id": "r1",
                "rank": 1,
                "explanation": "Great food and high rating",
            }
        ],
        "summary": "Sample summary",
    }
    resp = LLMRankingResponse(**payload)
    assert len(resp.recommendations) == 1
    assert resp.recommendations[0].restaurant_id == "r1"
    assert resp.summary == "Sample summary"
