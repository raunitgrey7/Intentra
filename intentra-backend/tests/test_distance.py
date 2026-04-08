from app.utils.distance import haversine_km


def test_haversine_returns_zero_for_same_point():
    assert haversine_km(28.6139, 77.2090, 28.6139, 77.2090) == 0


def test_haversine_returns_reasonable_distance():
    # New Delhi to Mumbai is roughly 1150km to 1200km by great-circle distance.
    distance = haversine_km(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1100 <= distance <= 1300
