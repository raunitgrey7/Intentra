import json
import os
import httpx
from app.models.response import Intent
from app.constants.mood_rules import DEFAULT_INTENT, infer_profile_from_query
from app.utils.cache import SimpleCache
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger("ai_service")
intent_cache = SimpleCache(ttl_seconds=600)

# Load API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ Correct, working Gemini model
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.5-flash:generateContent"
)

# 🔒 Strict system prompt (LLMs must be leashed)
SYSTEM_PROMPT = """
You are an intent extraction engine for a location recommendation system.

Your task is to return a SINGLE valid JSON object.
Do not include markdown.
Do not include code fences.
Do not include explanations.
Do not include any text before or after the JSON.

If you cannot determine a value, use reasonable defaults.

Return ONLY JSON in this exact schema:

{
    "mood": "quiet | fun | amusement | work | date | quick_bite | budget | explore",
  "place_types": ["string"],
  "radius_km": number,
  "min_rating": number,
  "preferences": ["string"]
}
""".strip()


def normalize_intent(user_query: str, intent_data: dict | None) -> Intent:
        profile = infer_profile_from_query(user_query)

        merged = dict(DEFAULT_INTENT)
        if intent_data:
                merged.update(intent_data)

        if profile:
                merged["mood"] = profile["mood"]
                merged["radius_km"] = max(float(merged.get("radius_km", 0)), float(profile["radius_km"]))
                merged["min_rating"] = max(float(merged.get("min_rating", 0)), float(profile["min_rating"]))
                merged["place_types"] = profile["place_types"] + merged.get("place_types", [])
                merged["preferences"] = profile["preferences"] + merged.get("preferences", [])

        merged["place_types"] = list(dict.fromkeys(merged.get("place_types", [])))[:6]
        merged["preferences"] = list(dict.fromkeys(merged.get("preferences", [])))[:6]

        # Clamp numeric fields for safety.
        merged["radius_km"] = min(max(float(merged.get("radius_km", 3.0)), 1.0), 25.0)
        merged["min_rating"] = min(max(float(merged.get("min_rating", 4.0)), 1.0), 5.0)

        return Intent(**merged)


def extract_json(text: str) -> dict:
    """
    Safely extracts the first valid JSON object from Gemini output.
    Handles markdown, extra text, or partial responses.
    """
    if not text:
        raise ValueError("Empty Gemini response")

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in Gemini response")

    json_str = text[start:end + 1]
    return json.loads(json_str)


async def extract_intent(user_query: str) -> Intent:
    """
    Extract structured intent from free text using Gemini.
    Uses caching and always fails safely.
    """

    # 1️⃣ Cache check
    cache_key = user_query.strip().lower()
    cached_intent = intent_cache.get(cache_key)
    if cached_intent:
        logger.info("Intent cache hit")
        return cached_intent

    logger.info("Intent cache miss – calling Gemini")

    # 2️⃣ API key check
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set, using fallback intent")
        return normalize_intent(user_query, None)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": SYSTEM_PROMPT},
                    {"text": f"User input: {user_query}"}
                ]
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    try:
        timeout = get_settings().external_api_timeout_seconds
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                headers=headers,
                json=payload
            )

        response.raise_for_status()

        # 3️⃣ Safely read model output
        text_output = (
            response.json()
            .get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        # 4️⃣ Hardened JSON extraction
        intent_dict = extract_json(text_output)
        intent = normalize_intent(user_query, intent_dict)

        # 5️⃣ Cache + return
        intent_cache.set(cache_key, intent)
        logger.info("Intent extracted and cached via Gemini")

        return intent

    except Exception as e:
        logger.error(f"Gemini intent extraction failed: {e}")
        return normalize_intent(user_query, None)
