from app.models.response import ExperiencePlan, PlaceRecommendation, TripStep


MOOD_BEST_TIME = {
    "quiet": "Morning or late afternoon",
    "fun": "Evening",
    "amusement": "Weekend daytime",
    "work": "Weekday mornings",
    "date": "Sunset to early night",
    "quick_bite": "Anytime",
    "budget": "Off-peak hours",
    "explore": "Golden hour",
}


def build_experience_plan(mood: str, recommendations: list[PlaceRecommendation]) -> ExperiencePlan | None:
    if not recommendations:
        return None

    top = recommendations[:3]
    steps: list[TripStep] = []

    for index, place in enumerate(top, start=1):
        reason = (
            f"Step {index}: {place.name} fits this mood with a score of {place.score} "
            f"and is {place.distance_km} km away."
        )
        steps.append(
            TripStep(
                title=place.name,
                reason=reason,
                maps_url=place.maps_url,
            )
        )

    duration = 45 + (len(top) * 35)

    return ExperiencePlan(
        headline=f"{mood.capitalize()} trail with {len(top)} strong matches",
        best_time=MOOD_BEST_TIME.get(mood, "Anytime"),
        estimated_duration_minutes=duration,
        steps=steps,
    )
