from pydantic import BaseModel
from typing import List


class Intent(BaseModel):
    mood: str
    place_types: List[str]
    radius_km: float
    min_rating: float
    preferences: List[str]


class PlaceRecommendation(BaseModel):
    name: str
    lat: float
    lng: float
    distance_km: float
    rating: float
    open_now: bool
    score: float
    why: str
    category: str | None = None
    maps_url: str | None = None


class TripStep(BaseModel):
    title: str
    reason: str
    maps_url: str | None = None


class ExperiencePlan(BaseModel):
    headline: str
    best_time: str
    estimated_duration_minutes: int
    steps: List[TripStep]


class RecommendationInsights(BaseModel):
    diversity_index: float
    average_distance_km: float
    open_now_ratio: float
    top_category: str


class MatchupSummary(BaseModel):
    left_place: str
    right_place: str
    winner: str
    reason: str


class RecommendResponse(BaseModel):
    intent: Intent
    recommendations: List[PlaceRecommendation]
    plan: ExperiencePlan | None = None
    insights: RecommendationInsights | None = None
    matchup: MatchupSummary | None = None
