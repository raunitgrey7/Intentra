from fastapi.testclient import TestClient

from app.main import app
from app.models.response import Intent


client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body


def test_recommend_endpoint_returns_expected_shape(monkeypatch):
    async def fake_extract_intent(_query: str) -> Intent:
        return Intent(
            mood="explore",
            place_types=["cafe"],
            radius_km=3.0,
            min_rating=4.0,
            preferences=[],
        )

    async def fake_get_nearby_places(latitude: float, longitude: float, intent: Intent):
        return [
            {
                "name": "Test Cafe",
                "lat": latitude,
                "lng": longitude,
                "rating": 4.5,
                "open_now": True,
                "types": intent.place_types,
            }
        ]

    monkeypatch.setattr("app.api.routes.recommend.extract_intent", fake_extract_intent)
    monkeypatch.setattr("app.api.routes.recommend.get_nearby_places", fake_get_nearby_places)

    response = client.post(
        "/recommend",
        json={
            "query": "quiet cafe for work",
            "latitude": 28.6139,
            "longitude": 77.2090,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["intent"]["mood"] == "explore"
    assert len(body["recommendations"]) == 1
    assert body["recommendations"][0]["name"] == "Test Cafe"
    assert body["plan"] is not None
    assert "headline" in body["plan"]
    assert body["insights"] is not None


def test_recommend_endpoint_applies_open_and_distance_filters(monkeypatch):
    async def fake_extract_intent(_query: str) -> Intent:
        return Intent(
            mood="explore",
            place_types=["cafe"],
            radius_km=10.0,
            min_rating=4.0,
            preferences=[],
        )

    async def fake_get_nearby_places(latitude: float, longitude: float, intent: Intent):
        return [
            {
                "name": "Near Open Cafe",
                "lat": latitude,
                "lng": longitude,
                "rating": 4.3,
                "open_now": True,
                "types": intent.place_types,
                "category": "cafe",
            },
            {
                "name": "Far Closed Cafe",
                "lat": 28.9000,
                "lng": 77.5000,
                "rating": 4.7,
                "open_now": False,
                "types": ["cafe"],
                "category": "cafe",
            },
        ]

    monkeypatch.setattr("app.api.routes.recommend.extract_intent", fake_extract_intent)
    monkeypatch.setattr("app.api.routes.recommend.get_nearby_places", fake_get_nearby_places)

    response = client.post(
        "/recommend",
        json={
            "query": "great cafe",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "max_distance_km": 3,
            "open_now_only": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["recommendations"]) == 1
    assert body["recommendations"][0]["name"] == "Near Open Cafe"
