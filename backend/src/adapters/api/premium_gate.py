"""Premium gate middleware for protecting premium-only endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request


def require_premium(request: Request) -> dict[str, Any]:
    """FastAPI dependency that gates access to premium-only endpoints.

    Checks for a valid premium subscription marker in the request.
    In Wave 7, this will integrate with JWT auth. For now it checks
    the X-Premium-Token header as a simple gate.
    """
    token = request.headers.get("X-Premium-Token")
    if not token:
        raise HTTPException(
            status_code=403,
            detail="Premium subscription required. Subscribe at /pro.",
        )
    # Placeholder — Wave 7 will validate JWT and check subscription status
    return {"premium": True, "token": token}
