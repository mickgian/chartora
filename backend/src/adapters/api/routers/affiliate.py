"""Affiliate link click-tracking router."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/affiliate", tags=["affiliate"])

# Broker destination URLs — kept server-side so affiliate IDs stay private
BROKER_URLS: dict[str, str] = {
    "ibkr": "https://www.interactivebrokers.com/mkt/?src=chartora&conid={ticker}",
    "etoro": "https://www.etoro.com/markets/{ticker}?utm_source=chartora&utm_medium=affiliate",
}


@router.get("/click")
async def track_affiliate_click(
    request: Request,
    broker: str = Query(..., description="Broker slug"),
    ticker: str = Query(..., description="Stock ticker"),
    company: str = Query(..., description="Company slug"),
) -> Any:
    """Log an affiliate click and return the destination URL.

    In production this would redirect (302). We return JSON so the
    frontend can open the link in a new tab while we record the event.
    """
    logger.info(
        "affiliate_click broker=%s ticker=%s company=%s ip=%s",
        broker,
        ticker,
        company,
        request.client.host if request.client else "unknown",
    )

    template = BROKER_URLS.get(broker)
    if template is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Unknown broker: {broker}"},
        )

    destination = template.replace("{ticker}", ticker)
    return {"destination": destination, "broker": broker, "ticker": ticker}
