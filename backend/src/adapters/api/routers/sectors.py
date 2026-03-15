"""Sector management API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.domain.models.sector_config import DEFAULT_QUANTUM_SECTOR

if TYPE_CHECKING:
    from src.domain.models.sector_config import SectorConfig

router = APIRouter(prefix="/api/v1/sectors", tags=["sectors"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class SectorResponse(BaseModel):
    """Pydantic response model for a sector configuration."""

    name: str
    display_name: str
    slug: str
    description: str
    score_weights: dict[str, float]
    enabled: bool


class SectorListResponse(BaseModel):
    """Pydantic response model for listing sectors."""

    sectors: list[SectorResponse]
    total: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sector_to_response(sector_config: SectorConfig) -> SectorResponse:
    """Convert a SectorConfig domain model to a response model.

    Args:
        sector_config: A SectorConfig dataclass instance.

    Returns:
        A SectorResponse pydantic model.
    """
    return SectorResponse(
        name=sector_config.name,
        display_name=sector_config.display_name,
        slug=sector_config.slug,
        description=sector_config.description,
        score_weights=sector_config.score_weights,
        enabled=sector_config.enabled,
    )


# Hardcoded sectors for initial implementation
_SECTORS = [DEFAULT_QUANTUM_SECTOR]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=SectorListResponse)
async def list_sectors() -> SectorListResponse:
    """List all available sector configurations.

    Returns all tracked sectors with their scoring weights and metadata.
    """
    sector_responses = [_sector_to_response(s) for s in _SECTORS]
    return SectorListResponse(
        sectors=sector_responses,
        total=len(sector_responses),
    )


@router.get("/{slug}", response_model=SectorResponse)
async def get_sector(slug: str) -> SectorResponse:
    """Get detailed configuration for a specific sector.

    Args:
        slug: The URL-friendly identifier for the sector.

    Returns:
        The sector configuration with scoring weights.

    Raises:
        HTTPException: 404 if the sector slug is not found.
    """
    for sector in _SECTORS:
        if sector.slug == slug:
            return _sector_to_response(sector)

    raise HTTPException(
        status_code=404,
        detail=f"Sector with slug '{slug}' not found",
    )
