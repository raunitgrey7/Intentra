import asyncio
import httpx
import random
from typing import List
from app.models.response import Intent
from app.utils.cache import SimpleCache
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger("places_service")
places_cache = SimpleCache(ttl_seconds=300)

# Multiple Overpass mirrors for reliability
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

# Intent → OSM tag mapping
# NOTE: Mapping is intentionally practical, not academic
INTENT_TO_OSM = {
    "cafe": {"amenity": "cafe"},
    "restaurant": {"amenity": "restaurant"},
    "fast_food": {"amenity": "fast_food"},
    "bar": {"amenity": "bar"},
    "coworking": {"amenity": "coworking_space"},
    "library": {"amenity": "library"},
    "park": {"leisure": "park"},
    "cinema": {"amenity": "cinema"},
    "arcade": {"leisure": "amusement_arcade"},
    "amusement_park": {"tourism": "theme_park"},
    "water_park": {"leisure": "water_park"},
    "zoo": {"tourism": "zoo"},
}

# Fallback tags when strict intent yields zero results
FALLBACK_OSM_TAGS = [
    {"amenity": "cafe"},
    {"amenity": "restaurant"},
    {"leisure": "park"},
]


def _extract_coordinates(element: dict) -> tuple[float, float] | tuple[None, None]:
    lat = element.get("lat")
    lng = element.get("lon")
    if lat is not None and lng is not None:
        return lat, lng

    center = element.get("center", {})
    if center.get("lat") is not None and center.get("lon") is not None:
        return center["lat"], center["lon"]

    return None, None


def _estimate_rating(place_type: str, tags: dict) -> float:
    base_rating_by_type = {
        "library": 4.4,
        "park": 4.3,
        "coworking": 4.2,
        "cafe": 4.1,
        "restaurant": 4.1,
        "cinema": 4.2,
        "amusement_park": 4.3,
        "water_park": 4.1,
        "zoo": 4.2,
        "arcade": 4.0,
        "fast_food": 3.8,
        "bar": 3.9,
        "fallback": 4.0,
    }
    rating = base_rating_by_type.get(place_type, 4.0)

    if tags.get("operator") or tags.get("brand"):
        rating += 0.05
    if tags.get("wheelchair") == "yes":
        rating += 0.05
    if tags.get("internet_access") in {"wlan", "yes"}:
        rating += 0.05

    return min(5.0, round(rating, 2))


def _build_place_record(element: dict, place_type: str) -> dict | None:
    lat, lng = _extract_coordinates(element)
    if lat is None or lng is None:
        return None

    tags = element.get("tags", {})
    name = tags.get("name", "Nearby place")
    opening_hours = tags.get("opening_hours", "")
    open_now = "24/7" in opening_hours or opening_hours == ""

    return {
        "name": name,
        "lat": lat,
        "lng": lng,
        "rating": _estimate_rating(place_type, tags),
        "open_now": open_now,
        "types": [place_type],
        "category": place_type,
        "maps_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}#map=17/{lat}/{lng}",
    }


def _dedupe_places(places: List[dict]) -> List[dict]:
    seen = set()
    unique: List[dict] = []
    for place in places:
        key = (
            place.get("name", "").strip().lower(),
            round(float(place.get("lat", 0.0)), 5),
            round(float(place.get("lng", 0.0)), 5),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(place)

    return unique


def _build_emergency_fallback(latitude: float, longitude: float, intent: Intent) -> List[dict]:
    # Last-resort local candidates so UI always has actionable results.
    offsets = [(0.004, 0.004), (-0.004, 0.003), (0.003, -0.004)]
    base_category = intent.place_types[0] if intent.place_types else "fallback"
    emergency = []

    for index, (lat_off, lng_off) in enumerate(offsets, start=1):
        lat = latitude + lat_off
        lng = longitude + lng_off
        emergency.append(
            {
                "name": f"Suggested {base_category.replace('_', ' ')} #{index}",
                "lat": lat,
                "lng": lng,
                "rating": 4.0,
                "open_now": True,
                "types": [base_category],
                "category": "fallback",
                "maps_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}#map=17/{lat}/{lng}",
            }
        )

    return emergency


def build_overpass_query(lat: float, lon: float, radius_m: int, tags: dict) -> str:
    tag_filters = "".join(
        [f'["{k}"="{v}"]' for k, v in tags.items()]
    )

    return f"""
    [out:json][timeout:6];
        (
            node
            {tag_filters}
            (around:{radius_m},{lat},{lon});
            way
      {tag_filters}
      (around:{radius_m},{lat},{lon});
            relation
            {tag_filters}
            (around:{radius_m},{lat},{lon});
        );
        out center 30;
    """


async def query_overpass(query: str, max_mirrors: int | None = None) -> List[dict]:
    """
    Query Overpass using multiple mirrors until one succeeds.
    """
    settings = get_settings()
    mirror_cap = max_mirrors or settings.overpass_max_mirrors_per_query
    mirrors = OVERPASS_URLS.copy()
    random.shuffle(mirrors)

    for url in mirrors[:mirror_cap]:
        try:
            timeout = settings.external_api_timeout_seconds
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, data=query)

            response.raise_for_status()
            logger.info(f"Overpass success via {url}")
            return response.json().get("elements", [])

        except Exception as e:
            logger.error(f"Overpass failed via {url}: {e}")

    return []


async def get_nearby_places(
    latitude: float,
    longitude: float,
    intent: Intent
) -> List[dict]:
    """
    Fetch nearby places using OpenStreetMap Overpass API
    with progressive relaxation for sparse data.
    """

    place_types_key = "|".join(sorted(intent.place_types))
    cache_key = f"{latitude}:{longitude}:{place_types_key}:{intent.radius_km}"
    cached = places_cache.get(cache_key)

    if cached is not None:
        logger.info("OSM places cache hit")
        return cached

    logger.info("OSM cache miss – querying Overpass")

    settings = get_settings()
    places: List[dict] = []
    radius_m = int(intent.radius_km * 1000)
    selected_place_types = intent.place_types[: settings.max_place_types_per_query]

    async def fetch_for_place_type(place_type: str) -> List[dict]:
        tags = INTENT_TO_OSM.get(place_type)
        if not tags:
            return []

        query = build_overpass_query(
            latitude,
            longitude,
            radius_m,
            tags
        )

        elements = await query_overpass(query)
        records: List[dict] = []
        for el in elements:
            record = _build_place_record(el, place_type)
            if record:
                records.append(record)
        return records

    # 1️⃣ STRICT INTENT QUERY
    tasks = [asyncio.create_task(fetch_for_place_type(place_type)) for place_type in selected_place_types]
    done, pending = await asyncio.wait(tasks, timeout=settings.external_api_timeout_seconds * 2)

    for task in done:
        try:
            places.extend(task.result())
        except Exception as exc:
            logger.error(f"Place-type query task failed: {exc}")

    for task in pending:
        task.cancel()

    if pending:
        logger.warning(f"Cancelled {len(pending)} slow place-type queries to protect response time")

    # 2️⃣ FALLBACK RELAXATION (CRITICAL FOR OSM REALITY)
    if not places:
        logger.info(
            f"No places found for strict intent '{intent.mood}'. "
            "Relaxing constraints using fallback categories."
        )

        async def fetch_fallback(tags: dict) -> List[dict]:
            fallback_query = build_overpass_query(
                latitude,
                longitude,
                radius_m,
                tags,
            )
            elements = await query_overpass(fallback_query, max_mirrors=1)
            fallback_records: List[dict] = []
            for el in elements:
                record = _build_place_record(el, "fallback")
                if record:
                    fallback_records.append(record)
            return fallback_records

        fallback_tasks = [asyncio.create_task(fetch_fallback(tags)) for tags in FALLBACK_OSM_TAGS]
        done_fb, pending_fb = await asyncio.wait(
            fallback_tasks,
            timeout=settings.fallback_phase_timeout_seconds,
        )

        for task in done_fb:
            try:
                places.extend(task.result())
            except Exception as exc:
                logger.error(f"Fallback task failed: {exc}")

        for task in pending_fb:
            task.cancel()

        if pending_fb:
            logger.warning(f"Cancelled {len(pending_fb)} slow fallback tasks to protect response time")

        if places:
            logger.info("Fallback query returned results")

    if not places:
        logger.warning("All Overpass queries failed or returned empty. Using emergency fallback places.")
        places = _build_emergency_fallback(latitude, longitude, intent)

    unique_places = _dedupe_places(places)
    places_cache.set(cache_key, unique_places)
    logger.info(f"Cached {len(unique_places)} OSM places")

    return unique_places
