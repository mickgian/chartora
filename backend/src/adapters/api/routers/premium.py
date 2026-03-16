"""Premium-only API endpoints for historical data, alerts, and exports."""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from src.adapters.api.dependencies import (  # noqa: TC001
    AlertPrefRepoDep,
    ApiKeyRepoDep,
    CompanyRepoDep,
    FilingRepoDep,
    GovContractRepoDep,
    PatentRepoDep,
    ScoreRepoDep,
)
from src.adapters.api.premium_gate import require_premium
from src.domain.models.entities import AlertPreference, ApiKey
from src.domain.models.value_objects import DateRange
from src.infrastructure.auth import generate_api_key
from src.infrastructure.sec_edgar_xbrl import SecEdgarXbrlAdapter

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/pro",
    tags=["premium"],
    dependencies=[Depends(require_premium)],
)


# ──────────────────────────────────────────────
# W7.2 — Historical Data Views
# ──────────────────────────────────────────────


@router.get("/historical-scores/{slug}")
async def get_historical_scores(
    slug: str,
    company_repo: CompanyRepoDep,
    score_repo: ScoreRepoDep,
    days: int = Query(default=365, ge=7, le=3650),
) -> dict[str, Any]:
    """Get historical Quantum Power Score for a company."""
    logger.info("[PREMIUM] historical-scores slug=%s days=%d", slug, days)
    company = await company_repo.get_by_slug(slug)
    if company is None:
        logger.warning("[PREMIUM] Company not found slug=%s", slug)
        raise HTTPException(status_code=404, detail="Company not found")

    end = date.today()
    start = end - timedelta(days=days)
    date_range = DateRange(start=start, end=end)

    scores = await score_repo.get_by_date_range(company.id, date_range)  # type: ignore[arg-type]
    logger.info(
        "[PREMIUM] historical-scores slug=%s returned %d scores",
        slug,
        len(scores),
    )
    return {
        "company_slug": slug,
        "company_name": company.name,
        "period_days": days,
        "scores": [
            {
                "date": s.score_date.isoformat(),
                "total_score": s.total_score,
                "stock_momentum": s.stock_momentum,
                "patent_velocity": s.patent_velocity,
                "qubit_progress": s.qubit_progress,
                "funding_strength": s.funding_strength,
                "news_sentiment": s.news_sentiment,
                "rank": s.rank,
            }
            for s in scores
        ],
        "count": len(scores),
    }


@router.get("/patents/{slug}/full-history")
async def get_full_patent_history(
    slug: str,
    company_repo: CompanyRepoDep,
    patent_repo: PatentRepoDep,
) -> dict[str, Any]:
    """Get full patent history for a company (premium-only)."""
    company = await company_repo.get_by_slug(slug)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    patents = await patent_repo.get_by_company(company.id)  # type: ignore[arg-type]
    return {
        "company_slug": slug,
        "company_name": company.name,
        "patents": [
            {
                "patent_number": p.patent_number,
                "title": p.title,
                "filing_date": p.filing_date.isoformat(),
                "grant_date": p.grant_date.isoformat() if p.grant_date else None,
                "source": p.source.value if hasattr(p.source, "value") else p.source,
                "abstract": p.abstract,
                "classification": p.classification,
            }
            for p in patents
        ],
        "count": len(patents),
    }


@router.get("/insider-trading/{slug}")
async def get_insider_trading(
    slug: str,
    company_repo: CompanyRepoDep,
    filing_repo: FilingRepoDep,
) -> dict[str, Any]:
    """Get insider trading history from Form 4 filings."""
    company = await company_repo.get_by_slug(slug)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    filings = await filing_repo.get_by_type(company.id, "Form4")  # type: ignore[arg-type]
    return {
        "company_slug": slug,
        "company_name": company.name,
        "insider_trades": [
            {
                "filing_date": f.filing_date.isoformat(),
                "description": f.description,
                "url": f.url,
                "data": json.loads(f.data_json) if f.data_json else None,
            }
            for f in filings
        ],
        "count": len(filings),
    }


@router.get("/institutional-ownership/{slug}")
async def get_institutional_ownership(
    slug: str,
    company_repo: CompanyRepoDep,
    filing_repo: FilingRepoDep,
) -> dict[str, Any]:
    """Get institutional ownership changes from 13F filings."""
    company = await company_repo.get_by_slug(slug)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    filings = await filing_repo.get_by_type(company.id, "13F")  # type: ignore[arg-type]
    return {
        "company_slug": slug,
        "company_name": company.name,
        "institutional_filings": [
            {
                "filing_date": f.filing_date.isoformat(),
                "description": f.description,
                "url": f.url,
                "data": json.loads(f.data_json) if f.data_json else None,
            }
            for f in filings
        ],
        "count": len(filings),
    }


# ──────────────────────────────────────────────
# Government Contracts & R&D Spending
# ──────────────────────────────────────────────


@router.get("/government-contracts/{slug}")
async def get_government_contracts(
    slug: str,
    company_repo: CompanyRepoDep,
    gov_contract_repo: GovContractRepoDep,
) -> dict[str, Any]:
    """Get government contracts for a company (premium-only)."""
    logger.info("[PREMIUM] government-contracts slug=%s", slug)
    company = await company_repo.get_by_slug(slug)
    if company is None:
        logger.warning("[PREMIUM] Company not found slug=%s", slug)
        raise HTTPException(status_code=404, detail="Company not found")

    contracts = await gov_contract_repo.get_by_company(company.id or 0)
    total_value = await gov_contract_repo.get_total_value(company.id or 0)
    logger.info(
        "[PREMIUM] government-contracts slug=%s contracts=%d total_value=%.2f",
        slug,
        len(contracts),
        total_value,
    )

    return {
        "company_slug": slug,
        "company_name": company.name,
        "contracts": [
            {
                "award_id": c.award_id,
                "title": c.title,
                "amount": float(c.amount),
                "awarding_agency": c.awarding_agency,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat() if c.end_date else None,
                "description": c.description,
            }
            for c in contracts
        ],
        "total_value": total_value,
        "count": len(contracts),
    }


@router.get("/rd-spending/{slug}")
async def get_rd_spending(
    slug: str,
    company_repo: CompanyRepoDep,
) -> dict[str, Any]:
    """Get R&D spending ratio for a company (premium-only)."""
    logger.info("[PREMIUM] rd-spending slug=%s", slug)
    company = await company_repo.get_by_slug(slug)
    if company is None:
        logger.warning("[PREMIUM] Company not found slug=%s", slug)
        raise HTTPException(status_code=404, detail="Company not found")

    if company.ticker is None:
        return {
            "company_slug": slug,
            "company_name": company.name,
            "rd_expense": None,
            "total_revenue": None,
            "rd_ratio": None,
            "message": "No ticker available for SEC EDGAR lookup",
        }

    xbrl_adapter = SecEdgarXbrlAdapter()
    rd_data = await xbrl_adapter.fetch_rd_spending(company.ticker.symbol)

    return {
        "company_slug": slug,
        "company_name": company.name,
        "rd_expense": rd_data["rd_expense"],
        "total_revenue": rd_data["total_revenue"],
        "rd_ratio": rd_data["rd_ratio"],
    }


# ──────────────────────────────────────────────
# W7.3 — Alerts
# ──────────────────────────────────────────────


@router.get("/alerts")
async def get_alert_preferences(
    request: Request,
    alert_repo: AlertPrefRepoDep,
) -> dict[str, Any]:
    """Get current user's alert preferences."""
    premium_info = await require_premium(request)
    user_id: int = premium_info["user_id"]

    prefs = await alert_repo.get_by_user(user_id)
    return {
        "alerts": [
            {
                "id": p.id,
                "alert_type": p.alert_type,
                "enabled": p.enabled,
                "threshold": p.threshold,
            }
            for p in prefs
        ],
    }


@router.put("/alerts")
async def update_alert_preferences(
    request: Request,
    alert_repo: AlertPrefRepoDep,
) -> dict[str, Any]:
    """Create or update alert preferences."""
    premium_info = await require_premium(request)
    user_id: int = premium_info["user_id"]

    body = await request.json()
    alerts: list[dict[str, Any]] = body.get("alerts", [])

    saved = []
    for alert_data in alerts:
        alert_type = alert_data.get("alert_type")
        if alert_type not in ("score_change", "insider_trading"):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid alert_type: {alert_type}",
            )

        # Find existing or create new
        existing = await alert_repo.get_by_user(user_id)
        pref = next((p for p in existing if p.alert_type == alert_type), None)

        if pref:
            pref.enabled = alert_data.get("enabled", True)
            pref.threshold = alert_data.get("threshold", pref.threshold)
            result = await alert_repo.save(pref)
        else:
            result = await alert_repo.save(
                AlertPreference(
                    user_id=user_id,
                    alert_type=alert_type,
                    enabled=alert_data.get("enabled", True),
                    threshold=alert_data.get("threshold"),
                )
            )
        saved.append(result)

    return {
        "alerts": [
            {
                "id": p.id,
                "alert_type": p.alert_type,
                "enabled": p.enabled,
                "threshold": p.threshold,
            }
            for p in saved
        ],
    }


# ──────────────────────────────────────────────
# W7.3 — Exports
# ──────────────────────────────────────────────


@router.get("/export/csv")
async def export_rankings_csv(
    company_repo: CompanyRepoDep,
    score_repo: ScoreRepoDep,
) -> StreamingResponse:
    """Export current rankings as CSV."""
    scores = await score_repo.get_latest_all()
    companies = await company_repo.get_all()
    company_map = {c.id: c for c in companies}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "rank",
            "company",
            "ticker",
            "sector",
            "total_score",
            "stock_momentum",
            "patent_velocity",
            "qubit_progress",
            "funding_strength",
            "news_sentiment",
            "score_date",
        ]
    )

    ranked = sorted(scores, key=lambda s: s.total_score, reverse=True)
    for rank_idx, score in enumerate(ranked, 1):
        company = company_map.get(score.company_id)
        writer.writerow(
            [
                rank_idx,
                company.name if company else "Unknown",
                str(company.ticker) if company and company.ticker else "",
                company.sector.value if company else "",
                score.total_score,
                score.stock_momentum,
                score.patent_velocity,
                score.qubit_progress,
                score.funding_strength,
                score.news_sentiment,
                score.score_date.isoformat(),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f"attachment; filename=chartora-rankings-{date.today().isoformat()}.csv"
            )
        },
    )


@router.get("/export/json")
async def export_rankings_json(
    company_repo: CompanyRepoDep,
    score_repo: ScoreRepoDep,
) -> dict[str, Any]:
    """Export current rankings as JSON."""
    scores = await score_repo.get_latest_all()
    companies = await company_repo.get_all()
    company_map = {c.id: c for c in companies}

    ranked = sorted(scores, key=lambda s: s.total_score, reverse=True)
    entries = []
    for rank_idx, score in enumerate(ranked, 1):
        company = company_map.get(score.company_id)
        entries.append(
            {
                "rank": rank_idx,
                "company": company.name if company else "Unknown",
                "ticker": str(company.ticker) if company and company.ticker else None,
                "sector": company.sector.value if company else None,
                "total_score": score.total_score,
                "stock_momentum": score.stock_momentum,
                "patent_velocity": score.patent_velocity,
                "qubit_progress": score.qubit_progress,
                "funding_strength": score.funding_strength,
                "news_sentiment": score.news_sentiment,
                "score_date": score.score_date.isoformat(),
            }
        )

    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "count": len(entries),
        "rankings": entries,
    }


# ──────────────────────────────────────────────
# W7.3 — API Key Management
# ──────────────────────────────────────────────


@router.get("/api-keys")
async def list_api_keys(
    request: Request,
    api_key_repo: ApiKeyRepoDep,
) -> dict[str, Any]:
    """List all API keys for the current user."""
    premium_info = await require_premium(request)
    user_id: int = premium_info["user_id"]

    keys = await api_key_repo.get_by_user(user_id)
    return {
        "api_keys": [
            {
                "id": k.id,
                "name": k.name,
                "prefix": k.prefix,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "is_active": k.is_active,
            }
            for k in keys
        ],
    }


@router.post("/api-keys")
async def create_api_key_endpoint(
    request: Request,
    api_key_repo: ApiKeyRepoDep,
) -> dict[str, Any]:
    """Create a new API key. Returns the full key only once."""
    premium_info = await require_premium(request)
    user_id: int = premium_info["user_id"]

    body = await request.json()
    name: str = body.get("name", "Default Key")

    full_key, key_hash, prefix = generate_api_key()

    api_key = ApiKey(
        user_id=user_id,
        key_hash=key_hash,
        name=name,
        prefix=prefix,
    )
    saved = await api_key_repo.save(api_key)

    return {
        "api_key": full_key,  # Only returned at creation time
        "id": saved.id,
        "name": saved.name,
        "prefix": saved.prefix,
        "message": "Save this key — it won't be shown again.",
    }


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    request: Request,
    api_key_repo: ApiKeyRepoDep,
) -> dict[str, str]:
    """Revoke (delete) an API key."""
    premium_info = await require_premium(request)
    user_id: int = premium_info["user_id"]

    keys = await api_key_repo.get_by_user(user_id)
    key = next((k for k in keys if k.id == key_id), None)
    if key is None:
        raise HTTPException(status_code=404, detail="API key not found")

    await api_key_repo.delete(key_id)
    return {"message": "API key revoked."}
