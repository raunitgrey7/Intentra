from app.services.ai_service import normalize_intent


def test_quiet_query_prefers_quiet_types():
    intent = normalize_intent("I need a quiet place to read and focus", None)

    assert intent.mood == "quiet"
    assert "library" in intent.place_types
    assert "park" in intent.place_types


def test_amusement_query_prefers_theme_destinations():
    intent = normalize_intent("Find amusement park rides and water park fun", None)

    assert intent.mood == "amusement"
    assert "amusement_park" in intent.place_types
    assert "water_park" in intent.place_types
