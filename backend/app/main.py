from __future__ import annotations

import time
import uuid

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.api import routes_papers, routes_research
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.problem import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.security import verify_api_key

configure_logging()
_log = get_logger(__name__)
_settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{_settings.rate_limit_per_minute}/minute"],
)

app = FastAPI(title="CorpusAI API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind a request_id to structlog context for the duration of the request."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:
            _log.exception("request_failed")
            raise
        duration_ms = int((time.perf_counter() - start) * 1000)
        _log.info(
            "request_completed",
            status=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key", "Accept", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(
    routes_research.router,
    dependencies=[Depends(verify_api_key)],
)
app.include_router(
    routes_papers.router,
    dependencies=[Depends(verify_api_key)],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Minimal health endpoint. Does not leak model/config details."""
    return {"status": "ok"}
