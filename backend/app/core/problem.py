"""RFC 7807 problem-details responses.

Errors returned by the API have media type `application/problem+json` and
the shape: {type, title, status, detail, instance}. Validation errors
include a `errors` array with the offending field paths.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_MEDIA_TYPE = "application/problem+json"


def _problem(
    *,
    status: int,
    title: str,
    detail: str,
    instance: str,
    type_: str = "about:blank",
    **extras: Any,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
    }
    body.update(extras)
    return JSONResponse(
        status_code=status, content=body, media_type=PROBLEM_MEDIA_TYPE
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return _problem(
        status=exc.status_code,
        title=_status_title(exc.status_code),
        detail=str(exc.detail),
        instance=str(request.url.path),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _problem(
        status=422,
        title="Validation Error",
        detail="The request body failed validation.",
        instance=str(request.url.path),
        errors=[
            {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]}
            for err in exc.errors()
        ],
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return _problem(
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred.",
        instance=str(request.url.path),
    )


def _status_title(code: int) -> str:
    return {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        413: "Payload Too Large",
        422: "Validation Error",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }.get(code, "Error")
