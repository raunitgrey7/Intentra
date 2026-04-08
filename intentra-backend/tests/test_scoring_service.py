from app.models.response import Intent
from app.services.scoring_service import score_places


def test_score_places_orders_results_by_score_descending():
    intent = Intent(
        mood="explore",
        place_types=["cafe"],
        radius_km=3.0,
        min_rating=4.0,
        preferences=[],
    )

    places = [
        {
            "name": "Closer Cafe",
            "lat": 28.6140,
            "lng": 77.2091,
            "rating": 4.1,
            "open_now": True,
            "types": ["cafe"],
        },
        {
            "name": "Far Cafe",
            "lat": 28.7000,
            "lng": 77.3000,
            "rating": 4.8,
            "open_now": True,
            "types": ["cafe"],
        },
    ]

    recommendations = score_places(places, intent, user_lat=28.6139, user_lng=77.2090)

    assert len(recommendations) == 2
    assert recommendations[0].score >= recommendations[1].score


def test_score_places_returns_empty_when_user_coordinates_missing():
    intent = Intent(
        mood="explore",
        place_types=["cafe"],
        radius_km=3.0,
        min_rating=4.0,
        preferences=[],
    )

    places = [
        {
            "name": "Any Cafe",
            "lat": 28.6140,
            "lng": 77.2091,
            "rating": 4.1,
            "open_now": True,
            "types": ["cafe"],
        }
    ]

    recommendations = score_places(places, intent)
    assert recommendations == []
