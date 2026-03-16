# Chartora — API Summary Per Page

## Page 1 — Main Leaderboard (FREE)

| Data | API | Key | URL / Library |
|------|-----|-----|---------------|
| Stock price + 30/60/90d change | yfinance (Yahoo Finance) | None | `pip install yfinance` |
| Patent count last 12 months | USPTO PatentsView | None | `https://api.patentsview.org/patents/query` |
| Qubit count | Manual DB seed | — | Updated manually, rarely changes |
| Total funding raised | SEC EDGAR XBRL | None | `https://data.sec.gov/api/xbrl/companyfacts/CIK{number}.json` |
| Quantum Power Score | Internal calculation | — | Stored in PostgreSQL |

## Page 2 — Company Detail Pages (FREE)

| Data | API | Key | URL / Library |
|------|-----|-----|---------------|
| Stock chart 30/90/365d | yfinance | None | `pip install yfinance` |
| Patent timeline by month | USPTO PatentsView | None | `https://api.patentsview.org/patents/query` |
| Company milestones | Manual DB seed | — | Curated once, rarely updated |
| News headlines (5 latest) | NewsAPI | Yes (free) | `https://newsapi.org/v2/everything?q={company}` |
| News sentiment score | Claude API | Yes (~$2-5/mo) | `https://api.anthropic.com/v1/messages` |

## Page 3 — Metric Deep Dives (FREE)

| Data | API | Key | Notes |
|------|-----|-----|-------|
| All metrics | None | — | Reuses data already stored from Pages 1 & 2 |
| `/rankings/patents` | USPTO (already pulled) | None | — |
| `/rankings/stock-performance` | yfinance (already pulled) | None | — |
| `/rankings/funding` | SEC EDGAR (already pulled) | None | — |
| `/rankings/government-contracts` | USASpending.gov | None | `https://api.usaspending.gov/api/v2/search/spending_by_award/` |

No new API calls needed for most metrics. All data already in PostgreSQL from daily cron.

## Page 4 — Premium Dashboard (PAID)

| Data | API | Key | URL / Library |
|------|-----|-----|---------------|
| Historical Power Score (2yr) | Internal DB | — | Daily snapshots stored from day 1 |
| Full stock history (2yr) | yfinance | None | `ticker.history(period="2y")` |
| Full patent history | USPTO PatentsView | None | `https://api.patentsview.org/patents/query` |
| Insider trades (Form 4) | SEC EDGAR | None | `https://data.sec.gov/submissions/CIK{number}.json` |
| Institutional ownership (13F) | SEC EDGAR | None | `https://data.sec.gov/submissions/CIK{number}.json` |
| R&D spending ratio | SEC EDGAR XBRL | None | `https://data.sec.gov/api/xbrl/companyfacts/CIK{number}.json` |
| Government contracts | USASpending.gov | None | `https://api.usaspending.gov/api/v2/search/spending_by_award/` |
| Email alerts | Resend.com | Yes (free) | `https://api.resend.com/emails` |
| CSV/JSON export | Internal DB | — | FastAPI serialization endpoint |
| API access | Your FastAPI | — | API key auth middleware |

---

## All API Keys — Where to Get Them

| Service | Pages | Register At | Cost |
|---------|-------|-------------|------|
| NewsAPI | 2 | [newsapi.org](https://newsapi.org) | Free (100 req/day) |
| Claude API | 2 | [console.anthropic.com](https://console.anthropic.com) | ~$2-5/month |
| Resend.com | 4 | [resend.com](https://resend.com) | Free (3k emails/month) |
| Stripe | 4 | [stripe.com](https://stripe.com) | 1.4% + €0.25/tx |
| yfinance | 1, 2, 4 | None | $0 (pip install) |
| USPTO PatentsView | 1, 2, 3, 4 | None | $0 |
| SEC EDGAR | 1, 4 | None (add User-Agent header) | $0 |
| USASpending.gov | 3, 4 | None | $0 |

---

## SEC EDGAR — Required Header

All SEC requests must include a `User-Agent` header or they will be blocked:

```python
headers = {
    "User-Agent": "Chartora contact@chartora.io"
}
```

---

## API Endpoints Summary

### Backend Routes

| Method | Endpoint | Page | Auth | Description |
|--------|----------|------|------|-------------|
| GET | `/api/v1/leaderboard` | 1 | Free | Main leaderboard with Quantum Power Score |
| GET | `/api/v1/companies/{slug}` | 2 | Free | Company detail with score |
| GET | `/api/v1/companies/{slug}/stock` | 2 | Free | Stock price history (30/90/365d) |
| GET | `/api/v1/companies/{slug}/patents` | 2 | Free | Patent timeline |
| GET | `/api/v1/companies/{slug}/news` | 2 | Free | News headlines with sentiment |
| GET | `/api/v1/companies/{slug}/filings` | 2 | Free | SEC filings summary |
| GET | `/api/v1/rankings/patents` | 3 | Free | Companies ranked by patent velocity |
| GET | `/api/v1/rankings/stock-performance` | 3 | Free | Companies ranked by stock momentum |
| GET | `/api/v1/rankings/funding` | 3 | Free | Companies ranked by funding strength |
| GET | `/api/v1/rankings/sentiment` | 3 | Free | Companies ranked by news sentiment |
| GET | `/api/v1/rankings/government-contracts` | 3 | Free | Companies ranked by contract value |
| GET | `/api/v1/pro/historical-scores/{slug}` | 4 | Premium | Historical Quantum Power Score (2yr) |
| GET | `/api/v1/pro/patents/{slug}/full-history` | 4 | Premium | Full patent history |
| GET | `/api/v1/pro/insider-trading/{slug}` | 4 | Premium | Insider trades (Form 4) |
| GET | `/api/v1/pro/institutional-ownership/{slug}` | 4 | Premium | Institutional ownership (13F) |
| GET | `/api/v1/pro/rd-spending/{slug}` | 4 | Premium | R&D spending ratio |
| GET | `/api/v1/pro/government-contracts/{slug}` | 4 | Premium | Government contracts detail |
| GET | `/api/v1/pro/alerts` | 4 | Premium | Alert preferences |
| PUT | `/api/v1/pro/alerts` | 4 | Premium | Update alert preferences |
| GET | `/api/v1/pro/export/csv` | 4 | Premium | Export rankings as CSV |
| GET | `/api/v1/pro/export/json` | 4 | Premium | Export rankings as JSON |
| GET | `/api/v1/pro/api-keys` | 4 | Premium | List API keys |
| POST | `/api/v1/pro/api-keys` | 4 | Premium | Create API key |
| DELETE | `/api/v1/pro/api-keys/{key_id}` | 4 | Premium | Revoke API key |

### External API Calls (Data Pipeline)

| External API | Endpoint | Method | Rate Limit |
|-------------|----------|--------|------------|
| Yahoo Finance | `yfinance` Python lib | Library | Unofficial, ~2000/hr |
| USPTO PatentsView | `POST https://api.patentsview.org/patents/query` | REST | None published |
| NewsAPI.org | `GET https://newsapi.org/v2/everything` | REST | 100 req/day (free) |
| Claude API | `POST https://api.anthropic.com/v1/messages` | REST | Per plan |
| SEC EDGAR Submissions | `GET https://data.sec.gov/submissions/CIK{cik}.json` | REST | 10 req/sec |
| SEC EDGAR XBRL | `GET https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` | REST | 10 req/sec |
| SEC Company Tickers | `GET https://www.sec.gov/files/company_tickers.json` | REST | 10 req/sec |
| USASpending.gov | `POST https://api.usaspending.gov/api/v2/search/spending_by_award/` | REST | None published |
| Resend.com | `POST https://api.resend.com/emails` | REST | 3k emails/month (free) |

---

## Total Monthly API Cost

| Scenario | Cost |
|----------|------|
| Launch | ~$3-5/month (Claude API only) |
| At scale | ~$3-5/month (same — all others free) |

---

## Implementation Status

| Component | Status | File |
|-----------|--------|------|
| Yahoo Finance adapter | ✅ Done | `backend/src/infrastructure/yahoo_finance.py` |
| USPTO PatentsView adapter | ✅ Done | `backend/src/infrastructure/uspto_client.py` |
| NewsAPI adapter | ✅ Done | `backend/src/infrastructure/news_client.py` |
| Claude sentiment analyzer | ✅ Done | `backend/src/infrastructure/sentiment.py` |
| SEC EDGAR adapter (filings) | ✅ Done | `backend/src/infrastructure/sec_edgar.py` |
| SEC EDGAR XBRL adapter (funding/R&D) | ✅ Done | `backend/src/infrastructure/sec_edgar_xbrl.py` |
| USASpending.gov adapter | ✅ Done | `backend/src/infrastructure/usaspending_client.py` |
| Resend email service | ✅ Done | `backend/src/infrastructure/email_service.py` |
| Data refresh cron script | ✅ Done | `backend/scripts/refresh_data.py` |
| Frontend API client | ✅ Done | `frontend/src/lib/api-client.ts` |
