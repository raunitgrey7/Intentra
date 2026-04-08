from fastapi import APIRouter
from pydantic import BaseModel

from app.constants.mood_rules import MOOD_PROFILES

router = APIRouter(tags=["meta"])


class VibeCatalogResponse(BaseModel):
    vibes: list[dict]


@router.get("/vibes", response_model=VibeCatalogResponse)
def get_vibes() -> VibeCatalogResponse:
    vibes = []
    for mood, profile in MOOD_PROFILES.items():
        vibes.append(
            {
                "id": mood,
                "label": mood.replace("_", " ").title(),
                "sample_prompt": profile["keywords"][0] if profile.get("keywords") else mood,
                "place_types": profile.get("place_types", []),
            }
        )

    return VibeCatalogResponse(vibes=vibes)
