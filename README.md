Intentra Backend
Intentra is an intent-aware recommendation engine that turns a free-text user goal into ranked nearby places with explicit reasoning.

Core principle:

AI is used only for intent extraction.
Deterministic backend logic handles ranking and output.
What This Service Does
Accepts user query and location.
Extracts structured intent from natural language via Gemini.
Fetches places from OpenStreetMap Overpass API.
Ranks places by weighted score (rating, distance, open status).
Returns explainable recommendations.
Architecture
Flow:

Client calls POST /recommend.
ai_service extracts intent and caches it.
places_service fetches nearby OSM places with fallback categories.
scoring_service ranks and explains recommendations.
API returns structured response.
Production-Ready Elements Added
Centralized typed config (app/core/config.py).
Request context middleware with:
X-Request-ID
X-Process-Time-Ms
timeout guard returning 504.
Health endpoint GET /health.
Global exception handlers with consistent error payload shape.
Thread-safe in-memory cache.
Dependency pinning in requirements.txt.
Test suite for utility, scoring, and API contract.
Docker support (Dockerfile, .dockerignore).
CI workflow (.github/workflows/backend-ci.yml) for lint + tests.
These changes are additive and do not change recommendation core behavior.

Standout Product Features Added
Hybrid intent intelligence (AI + deterministic mood profiles) for clearer separation between quiet/fun/amusement scenarios.
Advanced controls in request payload:
max_distance_km
open_now_only
surprise_mode
Generated experience plan (plan) for action-oriented trips.
Recommendation analytics (insights) with diversity/open-now/distance metrics.
Head-to-head recommendation explanation (matchup) for fast decision-making.
Vibe catalog endpoint GET /vibes for dynamic UI chips.
API Reference
POST /recommend
Request body:

{
  "query": "quiet cafe for work",
  "latitude": 28.6139,
  "longitude": 77.2090
}
Response body (shape):

{
  "intent": {
    "mood": "explore",
    "place_types": ["cafe"],
    "radius_km": 3.0,
    "min_rating": 4.0,
    "preferences": []
  },
  "recommendations": [
    {
      "name": "Example Place",
      "lat": 28.614,
      "lng": 77.209,
      "distance_km": 0.2,
      "rating": 4.4,
      "open_now": true,
      "score": 0.87,
      "why": "Rated 4.4, 12 minutes away, open now"
    }
  ]
}
GET /health
Readiness/liveness endpoint for infra checks.

Local Setup
Create and activate a Python environment.
Install dependencies:
pip install -r requirements.txt
Copy .env.example to .env and fill values:
Required:

GEMINI_API_KEY
Optional:

APP_NAME
ENVIRONMENT
DEBUG
CORS_ORIGINS
REQUEST_TIMEOUT_SECONDS
LOG_LEVEL
Run the server:
uvicorn app.main:app --reload
Server URL:

API docs: http://localhost:8000/docs
Static UI: http://localhost:8000/
Testing and Linting
Run tests:

pytest -q
Run lint:

ruff check .
Docker
Build image:

docker build -t intentra-backend .
Run container:

docker run --rm -p 8000:8000 --env-file .env intentra-backend
Notes
Overpass data may have sparse metadata depending on location.
Ratings/open status for OSM are currently heuristic defaults.
Fallback tags are intentionally used to avoid zero-result responses.
