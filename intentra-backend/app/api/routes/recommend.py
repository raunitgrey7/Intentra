from fastapi import APIRouter
import random
from app.models.request import RecommendRequest
from app.models.response import RecommendResponse
from app.services.ai_service import extract_intent
from app.services.places_service import get_nearby_places
from app.services.scoring_service import score_places
from app.services.experience_service import build_experience_plan
from app.services.insights_service import build_matchup, build_recommendation_insights
from app.core.logger import get_logger

logger = get_logger("recommend_api")

router = APIRouter()


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_places(payload: RecommendRequest):
    logger.info("Received recommendation request")

    intent = await extract_intent(payload.query)

    places = await get_nearby_places(
        latitude=payload.latitude,
        longitude=payload.longitude,
        intent=intent
    )

    recommendations = score_places(
        places,
        intent,
        user_lat=payload.latitude,
        user_lng=payload.longitude
    )

    if payload.open_now_only:
        recommendations = [item for item in recommendations if item.open_now]

    if payload.max_distance_km is not None:
        recommendations = [
            item for item in recommendations if item.distance_km <= payload.max_distance_km
        ]

    if payload.surprise_mode and recommendations:
        # Keep top suggestions near the front while still introducing novelty.
        top = recommendations[:2]
        rest = recommendations[2:]
        random.Random(payload.query).shuffle(rest)
        recommendations = top + rest

    plan = build_experience_plan(intent.mood, recommendations)
    insights = build_recommendation_insights(recommendations)
    matchup = build_matchup(recommendations)

    logger.info("Returning recommendations")

    return RecommendResponse(
        intent=intent,
        recommendations=recommendations,
        plan=plan,
        insights=insights,
        matchup=matchup,
    )
