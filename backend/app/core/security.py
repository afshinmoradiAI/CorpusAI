"""Auth + per-user identity dependencies.

- `verify_api_key`: gates access via `X-API-Key`.
- `current_user_id`: returns the caller's user ID from `X-User-ID`. If unset,
  returns None (anonymous / dev mode); routes treat that as "no scoping".
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.config import get_settings

_MAX_USER_ID_LEN = 128


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = get_settings().app_api_key
    if not expected:
        return
    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


async def current_user_id(
    x_user_id: str | None = Header(default=None),
) -> str | None:
    if not x_user_id:
        return None
    cleaned = x_user_id.strip()
    if not cleaned:
        return None
    if len(cleaned) > _MAX_USER_ID_LEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"X-User-ID exceeds {_MAX_USER_ID_LEN} characters",
        )
    return cleaned
