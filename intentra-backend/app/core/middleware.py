import asyncio
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger("request_middleware")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        started_at = time.perf_counter()
        try:
            settings = get_settings()
            if request.url.path == "/recommend":
                response = await call_next(request)
            else:
                response = await asyncio.wait_for(call_next(request), timeout=settings.request_timeout_seconds)
        except asyncio.TimeoutError:
            logger.error("request timed out", extra={"request_id": request_id})
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timed out", "request_id": request_id},
            )

        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)

        logger.info(
            "%s %s -> %s in %sms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
