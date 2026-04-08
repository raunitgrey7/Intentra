from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        description="Free text describing user's intent or mood"
    )
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    max_distance_km: float | None = Field(default=None, gt=0, le=25)
    open_now_only: bool = False
    surprise_mode: bool = False
