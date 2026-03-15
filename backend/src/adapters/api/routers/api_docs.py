"""API documentation endpoints providing machine-readable docs."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/docs", tags=["documentation"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class EndpointInfo(BaseModel):
    """Description of a single API endpoint."""

    method: str
    path: str
    summary: str
    auth_required: bool = False


class EndpointListResponse(BaseModel):
    """Response containing all available API endpoints."""

    endpoints: list[EndpointInfo]


class SchemaField(BaseModel):
    """A single field within a schema."""

    name: str
    type: str
    required: bool = True
    description: str = ""


class SchemaInfo(BaseModel):
    """Description of a request or response schema."""

    name: str
    description: str
    fields: list[SchemaField]


class SchemaListResponse(BaseModel):
    """Response containing key request/response schemas."""

    schemas: list[SchemaInfo]


class RateLimitTier(BaseModel):
    """Rate limit configuration for a specific tier."""

    tier: str
    requests_per_minute: int
    requests_per_day: int
    description: str


class RateLimitResponse(BaseModel):
    """Response containing rate limiting information."""

    tiers: list[RateLimitTier]
    headers: dict[str, str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/endpoints", response_model=EndpointListResponse)
async def list_endpoints() -> EndpointListResponse:
    """Return a catalogue of all available API endpoints."""
    endpoints = [
        EndpointInfo(
            method="GET",
            path="/api/v1/companies",
            summary="List all tracked companies with current scores.",
        ),
        EndpointInfo(
            method="GET",
            path="/api/v1/companies/{slug}",
            summary="Get detailed information for a single company.",
        ),
        EndpointInfo(
            method="GET",
            path="/api/v1/rankings",
            summary="Get the full leaderboard ranked by Quantum Power Score.",
        ),
        EndpointInfo(
            method="GET",
            path="/api/v1/rankings/{metric}",
            summary="Get rankings for a specific metric.",
        ),
        EndpointInfo(
            method="GET",
            path="/api/v1/sectors",
            summary="List all available sector configurations.",
        ),
        EndpointInfo(
            method="GET",
            path="/api/v1/sectors/{slug}",
            summary="Get details for a specific sector.",
        ),
        EndpointInfo(
            method="GET",
            path="/api/v1/docs/endpoints",
            summary="List all available API endpoints.",
        ),
        EndpointInfo(
            method="GET",
            path="/api/v1/docs/schemas",
            summary="List key request and response schemas.",
        ),
        EndpointInfo(
            method="GET",
            path="/api/v1/docs/rate-limits",
            summary="Get rate limiting information.",
        ),
        EndpointInfo(
            method="GET",
            path="/api/v1/pro/dashboard",
            summary="Premium dashboard data.",
            auth_required=True,
        ),
        EndpointInfo(
            method="GET",
            path="/api/v1/pro/export",
            summary="Export data as CSV or JSON.",
            auth_required=True,
        ),
        EndpointInfo(
            method="POST",
            path="/api/v1/pro/alerts",
            summary="Create or update alert preferences.",
            auth_required=True,
        ),
    ]
    return EndpointListResponse(endpoints=endpoints)


@router.get("/schemas", response_model=SchemaListResponse)
async def list_schemas() -> SchemaListResponse:
    """Return key request and response schemas used by the API."""
    schemas = [
        SchemaInfo(
            name="Company",
            description="A tracked company entity.",
            fields=[
                SchemaField(
                    name="id",
                    type="integer",
                    description="Unique ID.",
                ),
                SchemaField(
                    name="name",
                    type="string",
                    description="Company name.",
                ),
                SchemaField(
                    name="slug",
                    type="string",
                    description="URL-friendly slug.",
                ),
                SchemaField(
                    name="sector",
                    type="string",
                    description="Sector: pure_play, big_tech, or etf.",
                ),
                SchemaField(
                    name="ticker",
                    type="string | null",
                    required=False,
                    description="Stock ticker symbol.",
                ),
                SchemaField(
                    name="description",
                    type="string | null",
                    required=False,
                    description="Brief company description.",
                ),
            ],
        ),
        SchemaInfo(
            name="QuantumPowerScore",
            description="Composite score ranking a company.",
            fields=[
                SchemaField(
                    name="company_id",
                    type="integer",
                    description="Associated company ID.",
                ),
                SchemaField(
                    name="total_score",
                    type="float",
                    description="Overall score from 0 to 100.",
                ),
                SchemaField(
                    name="stock_momentum",
                    type="float",
                    description="Stock performance component.",
                ),
                SchemaField(
                    name="patent_velocity",
                    type="float",
                    description="Patent filing velocity component.",
                ),
                SchemaField(
                    name="qubit_progress",
                    type="float",
                    description="Qubit milestone component.",
                ),
                SchemaField(
                    name="funding_strength",
                    type="float",
                    description="Funding strength component.",
                ),
                SchemaField(
                    name="news_sentiment",
                    type="float",
                    description="News sentiment component.",
                ),
                SchemaField(
                    name="calculated_at",
                    type="datetime",
                    description="Timestamp of calculation.",
                ),
            ],
        ),
        SchemaInfo(
            name="RankingEntry",
            description="A single row in the leaderboard.",
            fields=[
                SchemaField(
                    name="rank",
                    type="integer",
                    description="Position in leaderboard.",
                ),
                SchemaField(
                    name="company",
                    type="Company",
                    description="Company details.",
                ),
                SchemaField(
                    name="score",
                    type="QuantumPowerScore",
                    description="Current composite score.",
                ),
                SchemaField(
                    name="trend",
                    type="string",
                    description="Trend direction: up, down, or flat.",
                ),
            ],
        ),
    ]
    return SchemaListResponse(schemas=schemas)


@router.get("/rate-limits", response_model=RateLimitResponse)
async def get_rate_limits() -> RateLimitResponse:
    """Return rate limiting tiers and relevant HTTP headers."""
    tiers = [
        RateLimitTier(
            tier="anonymous",
            requests_per_minute=30,
            requests_per_day=500,
            description="Unauthenticated requests.",
        ),
        RateLimitTier(
            tier="free",
            requests_per_minute=60,
            requests_per_day=2000,
            description="Authenticated free-tier users.",
        ),
        RateLimitTier(
            tier="pro",
            requests_per_minute=120,
            requests_per_day=10000,
            description="Premium subscribers.",
        ),
    ]
    headers = {
        "X-RateLimit-Limit": "Maximum requests for the current window.",
        "X-RateLimit-Remaining": "Requests remaining in the current window.",
        "X-RateLimit-Reset": "UTC epoch seconds when the window resets.",
        "Retry-After": "Seconds to wait before retrying (sent on 429 responses).",
    }
    return RateLimitResponse(tiers=tiers, headers=headers)
