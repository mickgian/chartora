# Chartora — Development Roadmap

Tasks are organized in **waves** with explicit dependencies. Each wave can only start after all its dependencies from previous waves are complete. Within a wave, tasks can be worked on in parallel.

## Dependency Legend

- `→` means "depends on"
- `[Wn.m]` = Wave n, Task m
- Status: `[ ]` = pending, `[x]` = done

---

## Wave 0 — Project Foundation

> No dependencies. Must be completed first.

### [W0.1] Project scaffolding and tooling setup `[x]`
- Initialize Python backend with `pyproject.toml` (use `uv` or `poetry`)
- Configure `ruff` for linting and formatting
- Configure `mypy` for type checking
- Set up `pytest` with coverage
- Create backend directory structure per CLAUDE.md

### [W0.2] Frontend scaffolding `[x]`
- Initialize Next.js app with TypeScript + Tailwind CSS
- Configure ESLint + Prettier
- Set up Jest/Vitest for testing
- Create frontend directory structure per CLAUDE.md

### [W0.3] Database schema design `[x]`
- Design PostgreSQL schema for: companies, stock_prices, patents, scores, news, filings
- Write migration scripts (use Alembic)
- Write seed data for initial company list (IONQ, QBTS, RGTI, etc.)

### [W0.4] Docker and infrastructure setup `[x]`
- Create `docker-compose.yml` with PostgreSQL, backend, frontend services
- Create Dockerfiles for backend and frontend
- Create nginx config template
- Create `.env.example` with all required env vars

### [W0.5] CI/CD and pre-commit hooks `[x]`
- Set up pre-commit hooks (lint, type check, tests)
- Create GitHub Actions workflow for CI
- Configure branch protection rules

---

## Wave 1 — Domain Layer & Data Pipeline Core

> Depends on: W0.1, W0.3

### [W1.1] Domain models `[x]` → W0.1, W0.3
- Define domain entities: `Company`, `StockPrice`, `Patent`, `FundingRound`, `NewsArticle`, `QuantumPowerScore`
- Define value objects: `Ticker`, `ScoreComponent`, `DateRange`
- Write unit tests for all domain models
- No external dependencies — pure Python dataclasses/Pydantic models

### [W1.2] Repository interfaces (ports) `[x]` → W0.1
- Define abstract interfaces: `CompanyRepository`, `StockRepository`, `PatentRepository`, `ScoreRepository`, `NewsRepository`
- Define data source interfaces: `StockDataSource`, `PatentDataSource`, `NewsDataSource`, `FilingDataSource`
- Write interface contracts as tests

### [W1.3] Quantum Power Score algorithm `[x]` → W1.1
- Implement score calculation use case
- Weighted scoring: stock momentum (20%), patent velocity (25%), qubit progress (20%), funding strength (20%), news sentiment (15%)
- Normalize each component to 0-100 scale
- Write comprehensive unit tests with known inputs/outputs
- Test edge cases: missing data, zero values, single company

### [W1.4] Company ranking use case `[x]` → W1.1, W1.3
- Implement ranking logic: sort companies by Quantum Power Score
- Support ranking by individual metrics
- Calculate rank changes (up/down/flat)
- Write unit tests

---

## Wave 2 — Infrastructure Adapters (Data Sources)

> Depends on: W1.1, W1.2

### [W2.1] Yahoo Finance adapter `[ ]` → W1.2
- Implement `StockDataSource` using `yfinance`
- Fetch current price, market cap, 30/60/90 day performance
- Fetch historical OHLCV data (2+ years)
- Handle rate limiting and errors gracefully
- Write integration tests with mocked responses
- Write unit tests for data transformation

### [W2.2] USPTO Patent API adapter `[ ]` → W1.2
- Implement `PatentDataSource` for USPTO
- Search patents by company/assignee name
- Parse patent metadata: title, date, classification, abstract
- Calculate patent velocity (filings per 12 months)
- Write integration tests with mocked responses

### [W2.3] SEC EDGAR adapter `[ ]` → W1.2
- Implement `FilingDataSource` for SEC EDGAR
- Fetch 10-K/10-Q for R&D spending
- Fetch Form 4 for insider trading
- Fetch 13F for institutional ownership
- Parse XBRL/JSON filing data
- Write integration tests with mocked responses

### [W2.4] News API adapter `[ ]` → W1.2
- Implement `NewsDataSource` using NewsAPI.org
- Fetch recent headlines per company
- Alternative: GDELT Project as free fallback
- Write integration tests with mocked responses

### [W2.5] Sentiment analysis adapter `[ ]` → W1.2, W2.4
- Implement sentiment scoring for news articles
- Use Claude API for sentiment analysis
- Score each article: bullish/bearish/neutral + confidence
- Aggregate to company-level sentiment score
- Write unit tests with known sentiment inputs

### [W2.6] PostgreSQL repository implementations `[ ]` → W0.3, W1.2
- Implement all repository interfaces against PostgreSQL
- Use `asyncpg` or `psycopg3` for async DB access
- Write integration tests against test database
- Include migration runner

---

## Wave 3 — Backend API

> Depends on: W1.3, W1.4, W2.6

### [W3.1] FastAPI application setup `[ ]` → W0.1
- Create FastAPI app with dependency injection
- Set up CORS, error handling, request validation
- Configure OpenAPI docs
- Write health check endpoint with tests

### [W3.2] Leaderboard API endpoints `[ ]` → W1.4, W2.6, W3.1
- `GET /api/v1/leaderboard` — full ranking with scores
- `GET /api/v1/leaderboard?sort_by={metric}` — sort by specific metric
- `GET /api/v1/leaderboard?limit={n}` — top N companies
- Response includes: rank, company, score, trend, all metrics
- Write API tests

### [W3.3] Company detail API endpoints `[ ]` → W2.6, W3.1
- `GET /api/v1/companies/{slug}` — full company profile
- `GET /api/v1/companies/{slug}/stock` — stock price history
- `GET /api/v1/companies/{slug}/patents` — patent timeline
- `GET /api/v1/companies/{slug}/news` — recent news with sentiment
- `GET /api/v1/companies/{slug}/filings` — SEC filings summary
- Write API tests

### [W3.4] Rankings API endpoints `[ ]` → W1.4, W2.6, W3.1
- `GET /api/v1/rankings/patents` — companies ranked by patent count
- `GET /api/v1/rankings/stock-performance` — ranked by stock momentum
- `GET /api/v1/rankings/funding` — ranked by total funding
- `GET /api/v1/rankings/sentiment` — ranked by news sentiment
- Write API tests

### [W3.5] Data refresh orchestrator `[ ]` → W2.1, W2.2, W2.3, W2.4, W2.5, W2.6
- Create cron-compatible script that:
  1. Pulls fresh stock data from Yahoo Finance
  2. Pulls new patent filings from USPTO
  3. Pulls news headlines from NewsAPI
  4. Scores sentiment via Claude API
  5. Recalculates Quantum Power Score for all companies
  6. Stores everything in PostgreSQL
- Idempotent — safe to re-run
- Logging and error reporting
- Write integration tests

---

## Wave 4 — Frontend Core

> Depends on: W0.2, W3.2

### [W4.1] API client and types `[ ]` → W0.2, W3.2
- Create TypeScript types matching API responses
- Create API client module with fetch wrapper
- Handle errors, loading states, retries
- Write unit tests for API client

### [W4.2] Main Leaderboard page `[ ]` → W4.1
- Sortable data table with all companies
- Columns: Rank, Company, Score, Stock %, Patents, Funding, Sentiment, Trend
- Color-coded trend arrows (green up, red down, gray flat)
- Quantum Power Score badge with visual indicator
- "Last updated" timestamp
- Mobile responsive
- Write component tests

### [W4.3] Company detail page `[ ]` → W4.1
- Route: `/company/[slug]`
- Stock price chart (30/90/365 day toggle)
- Patent filing timeline chart
- Key milestones section
- News feed with sentiment badges
- Competitor comparison widget
- Write component tests

### [W4.4] Metric deep dive pages `[ ]` → W4.1
- Route: `/rankings/[metric]`
- Visual bar/column chart per metric
- Embeddable chart component (iframe-ready)
- Social share meta tags per page
- Write component tests

### [W4.5] Layout and navigation `[ ]` → W0.2
- Header with logo, nav links
- Footer with attribution, links
- Responsive sidebar/hamburger menu
- Dark/light mode toggle
- Loading skeletons
- Write component tests

---

## Wave 5 — SEO, Analytics & Deployment

> Depends on: W4.2, W4.3, W4.4, W4.5

### [W5.1] SEO optimization `[ ]` → W4.2, W4.3, W4.4
- Dynamic meta tags per page (title, description, OG image)
- Generate `sitemap.xml` dynamically from company list
- Add `robots.txt`
- Structured data (JSON-LD) for each company page
- Canonical URLs
- Write tests for meta tag generation

### [W5.2] Production deployment setup `[ ]` → W0.4, W3.5
- Finalize Docker Compose for production
- Nginx config with SSL termination (Let's Encrypt)
- Set up cron job for daily data refresh
- PostgreSQL backup script (pg_dump → Hetzner Object Storage)
- Health monitoring endpoint
- Write deployment verification tests

### [W5.3] Analytics and monitoring `[ ]` → W5.2
- Add Plausible Analytics or Umami (privacy-friendly, self-hostable)
- Set up error tracking (Sentry free tier)
- API response time logging
- Database query performance monitoring

---

## Wave 6 — Monetization Layer

> Depends on: W5.1, W5.2

### [W6.1] Ad integration `[ ]` → W5.1
- Google AdSense integration
- Ad placement: sidebar, between sections, footer
- Responsive ad units
- Ad-free detection for premium users
- Write tests to verify ad slots render correctly

### [W6.2] Affiliate link system `[ ]` → W4.2, W4.3
- "Trade [TICKER]" buttons next to each company
- Affiliate links to brokers (Interactive Brokers, eToro)
- Click tracking for conversion analytics
- Disclosure notice (FTC compliance)
- Write tests for link generation

### [W6.3] Stripe payment integration `[ ]` → W3.1
- Stripe Checkout for premium subscriptions
- Webhook handler for payment events
- User model with subscription status
- Premium gate middleware
- Write integration tests with Stripe test mode

---

## Wave 7 — Premium Features

> Depends on: W6.3

### [W7.1] User authentication `[ ]` → W6.3
- Email/password registration and login
- JWT token-based auth
- Password reset flow via Resend.com
- Write auth tests

### [W7.2] Historical data views `[ ]` → W7.1, W2.6
- Historical Quantum Power Score chart (backfilled + daily snapshots)
- Full patent history timeline
- Insider trading history table
- Institutional ownership changes over time
- Premium-gated API endpoints
- Write tests

### [W7.3] Alerts and exports `[ ]` → W7.1
- Email alerts when a company's score changes significantly (±10 points)
- Email alerts on insider trading activity
- CSV/JSON export of current rankings
- API access with API key management
- Write tests for alert triggers and export formats

### [W7.4] Ad-free premium experience `[ ]` → W7.1, W6.1
- Remove all ads for authenticated premium users
- Premium badge on profile
- Write tests

---

## Wave 8 — Growth & Polish

> Depends on: W7.1, W7.2, W7.3

### [W8.1] Social sharing and embeds `[ ]` → W5.1
- OG image generation (dynamic chart images for social previews)
- Embed code generator for charts
- Twitter/X card meta tags
- LinkedIn share optimization

### [W8.2] Performance optimization `[ ]` → W5.2
- API response caching (Redis or in-memory)
- Frontend static generation where possible (ISR)
- Image optimization
- Lighthouse score > 90
- Load testing with k6 or locust

### [W8.3] Content and landing pages `[ ]` → W5.1
- Landing page explaining Quantum Power Score methodology
- "About" page with credibility signals
- Blog/changelog page for updates
- Product Hunt launch page preparation

### [W8.4] Expansion preparation `[ ]` → W0.1
- Refactor data pipeline to support multiple sectors
- Abstract company tracker into reusable module
- Design plugin architecture for new data sources
- Document API for potential third-party integrations

---

## Wave Dependency Graph

```
Wave 0 (Foundation)
  ├── W0.1 Python scaffolding
  ├── W0.2 Frontend scaffolding
  ├── W0.3 Database schema
  ├── W0.4 Docker/infra
  └── W0.5 CI/CD & hooks
       │
Wave 1 (Domain) ← W0.1, W0.3
  ├── W1.1 Domain models
  ├── W1.2 Repository interfaces
  ├── W1.3 Score algorithm ← W1.1
  └── W1.4 Ranking logic ← W1.1, W1.3
       │
Wave 2 (Data Sources) ← W1.1, W1.2
  ├── W2.1 Yahoo Finance
  ├── W2.2 USPTO Patents
  ├── W2.3 SEC EDGAR
  ├── W2.4 News API
  ├── W2.5 Sentiment ← W2.4
  └── W2.6 PostgreSQL repos ← W0.3
       │
Wave 3 (Backend API) ← W1.3, W1.4, W2.6
  ├── W3.1 FastAPI setup
  ├── W3.2 Leaderboard API ← W3.1
  ├── W3.3 Company API ← W3.1
  ├── W3.4 Rankings API ← W3.1
  └── W3.5 Data refresh ← W2.*
       │
Wave 4 (Frontend) ← W0.2, W3.2
  ├── W4.1 API client
  ├── W4.2 Leaderboard page ← W4.1
  ├── W4.3 Company page ← W4.1
  ├── W4.4 Metric pages ← W4.1
  └── W4.5 Layout
       │
Wave 5 (Deploy) ← W4.*
  ├── W5.1 SEO
  ├── W5.2 Production deploy ← W0.4
  └── W5.3 Monitoring ← W5.2
       │
Wave 6 (Monetization) ← W5.*
  ├── W6.1 Ads
  ├── W6.2 Affiliates
  └── W6.3 Stripe
       │
Wave 7 (Premium) ← W6.3
  ├── W7.1 Auth
  ├── W7.2 Historical data ← W7.1
  ├── W7.3 Alerts & exports ← W7.1
  └── W7.4 Ad-free ← W7.1
       │
Wave 8 (Growth) ← W7.*
  ├── W8.1 Social sharing
  ├── W8.2 Performance
  ├── W8.3 Content pages
  └── W8.4 Expansion prep
```

---

## Estimated Timeline

| Wave | Description | Estimated Duration |
|------|-------------|--------------------|
| 0 | Foundation | 2-3 days |
| 1 | Domain Layer | 2-3 days |
| 2 | Data Sources | 3-5 days |
| 3 | Backend API | 2-3 days |
| 4 | Frontend | 3-5 days |
| 5 | Deployment | 1-2 days |
| 6 | Monetization | 2-3 days |
| 7 | Premium | 3-5 days |
| 8 | Growth | 2-3 days |
| **Total** | | **~20-32 days** |
