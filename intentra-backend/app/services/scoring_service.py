from typing import List
from app.models.response import PlaceRecommendation, Intent
from app.utils.distance import haversine_km
from app.core.logger import get_logger

logger = get_logger("scoring_service")


def score_places(
    places: List[dict],
    intent: Intent,
    user_lat: float = None,
    user_lng: float = None
) -> List[PlaceRecommendation]:
    """
    Scores and ranks places based on weighted logic.
    """

    logger.info(f"Scoring {len(places)} places for mood='{intent.mood}'")

    recommendations = []

    if user_lat is None or user_lng is None:
        logger.error("User coordinates missing, cannot score distance")
        return []

    for place in places:
        distance_km = haversine_km(
            user_lat,
            user_lng,
            place["lat"],
            place["lng"]
        )

        # Normalize values
        rating_score = place["rating"] / 5.0
        distance_score = max(0, 1 - (distance_km / intent.radius_km))
        open_score = 1.0 if place["open_now"] else 0.0
        place_types = set(place.get("types", []))
        requested_types = set(intent.place_types)
        type_match = len(place_types.intersection(requested_types)) / max(1, len(requested_types))

        # Weighted sum
        score = (
            rating_score * 0.42 +
            distance_score * 0.28 +
            open_score * 0.10 +
            type_match * 0.20
        )

        why = (
            f"Rated {place['rating']}, "
            f"{round(distance_km * 60)} minutes away, "
            f"{'open now' if place['open_now'] else 'currently closed'}, "
            f"intent match {round(type_match * 100)}%"
        )

        recommendations.append(
            PlaceRecommendation(
                name=place["name"],
                lat=place["lat"],
                lng=place["lng"],
                distance_km=round(distance_km, 2),
                rating=place["rating"],
                open_now=place["open_now"],
                score=round(score, 2),
                why=why,
                category=place.get("category"),
                maps_url=place.get("maps_url"),
            )
        )

    recommendations.sort(key=lambda x: x.score, reverse=True)
    logger.info("Scoring complete")

    return recommendations
