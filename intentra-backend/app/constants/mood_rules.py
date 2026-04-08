from typing import Any


DEFAULT_INTENT = {
    "mood": "explore",
    "place_types": ["restaurant", "cafe", "park"],
    "radius_km": 3.0,
    "min_rating": 4.0,
    "preferences": [],
}

MOOD_PROFILES: dict[str, dict[str, Any]] = {
    "quiet": {
        "keywords": [
            "quiet",
            "calm",
            "peaceful",
            "focus",
            "study",
            "read",
            "library",
            "work quietly",
        ],
        "place_types": ["library", "cafe", "coworking", "park"],
        "radius_km": 4.0,
        "min_rating": 4.0,
        "preferences": ["less crowd", "comfortable seating"],
    },
    "fun": {
        "keywords": [
            "fun",
            "party",
            "hangout",
            "night out",
            "gaming",
            "arcade",
            "bowling",
        ],
        "place_types": ["arcade", "amusement_park", "cinema", "bar"],
        "radius_km": 8.0,
        "min_rating": 3.8,
        "preferences": ["lively atmosphere"],
    },
    "amusement": {
        "keywords": [
            "amusement",
            "theme park",
            "water park",
            "rides",
            "roller coaster",
            "adventure park",
        ],
        "place_types": ["amusement_park", "water_park", "zoo"],
        "radius_km": 20.0,
        "min_rating": 3.8,
        "preferences": ["family friendly"],
    },
    "work": {
        "keywords": ["work", "meeting", "productivity", "wifi", "laptop"],
        "place_types": ["coworking", "library", "cafe"],
        "radius_km": 5.0,
        "min_rating": 4.0,
        "preferences": ["power outlets", "quiet"],
    },
    "date": {
        "keywords": ["date", "romantic", "anniversary", "dinner"],
        "place_types": ["restaurant", "park", "cafe", "cinema"],
        "radius_km": 6.0,
        "min_rating": 4.1,
        "preferences": ["ambience"],
    },
    "quick_bite": {
        "keywords": ["quick", "fast", "snack", "grab", "bite"],
        "place_types": ["fast_food", "cafe", "restaurant"],
        "radius_km": 2.5,
        "min_rating": 3.7,
        "preferences": ["fast service"],
    },
    "budget": {
        "keywords": ["budget", "cheap", "affordable", "low cost"],
        "place_types": ["fast_food", "restaurant", "park"],
        "radius_km": 4.0,
        "min_rating": 3.5,
        "preferences": ["value for money"],
    },
}


def infer_profile_from_query(query: str) -> dict[str, Any] | None:
    query_lc = query.lower()
    best_profile = None
    best_score = 0

    for mood, profile in MOOD_PROFILES.items():
        score = sum(1 for keyword in profile["keywords"] if keyword in query_lc)
        if score > best_score:
            best_score = score
            best_profile = {"mood": mood, **profile}

    return best_profile if best_score > 0 else None
