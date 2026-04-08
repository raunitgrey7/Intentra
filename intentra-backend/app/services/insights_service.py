from collections import Counter

from app.models.response import MatchupSummary, PlaceRecommendation, RecommendationInsights


def build_recommendation_insights(recommendations: list[PlaceRecommendation]) -> RecommendationInsights | None:
    if not recommendations:
        return None

    categories = [item.category or "unknown" for item in recommendations]
    counter = Counter(categories)
    distinct = len(counter)
    total = len(recommendations)

    diversity_index = round(distinct / total, 2)
    avg_distance = round(sum(item.distance_km for item in recommendations) / total, 2)
    open_now_count = sum(1 for item in recommendations if item.open_now)
    open_ratio = round(open_now_count / total, 2)
    top_category = counter.most_common(1)[0][0]

    return RecommendationInsights(
        diversity_index=diversity_index,
        average_distance_km=avg_distance,
        open_now_ratio=open_ratio,
        top_category=top_category,
    )


def build_matchup(recommendations: list[PlaceRecommendation]) -> MatchupSummary | None:
    if len(recommendations) < 2:
        return None

    left = recommendations[0]
    right = recommendations[1]

    winner = left if left.score >= right.score else right
    if winner is left:
        loser = right
    else:
        loser = left

    reason = (
        f"{winner.name} wins with score {winner.score} vs {loser.score}, "
        f"balancing distance and intent match better."
    )

    return MatchupSummary(
        left_place=left.name,
        right_place=right.name,
        winner=winner.name,
        reason=reason,
    )
