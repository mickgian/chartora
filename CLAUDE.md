# CLAUDE.md — Chartora Project Context

## What is Chartora?

Chartora is a Visual Capitalist-style auto-updating leaderboard for quantum computing companies, targeting investors. It ranks companies by a composite "Quantum Power Score" combining stock performance, patent filings, qubit milestones, funding, and news sentiment.

The goal: build once, let it run passively with daily auto-updating data, monetize through ads, affiliate links, and a premium tier.

## Target Audience

- Retail and institutional investors interested in quantum computing
- Financial analysts covering emerging tech sectors
- Tech researchers tracking quantum computing progress

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js + Tailwind CSS |
| Charts | Recharts or D3.js |
| Backend | FastAPI (Python) |
| Database | PostgreSQL (self-hosted on Hetzner) |
| Reverse Proxy | Nginx |
| SSL | Let's Encrypt (Certbot) |
| Cron | Linux cron for daily data refresh |
| Payments | Stripe |
| Email | Resend.com (free tier) |
| Hosting | Hetzner CX22 VPS (Ubuntu 24.04) |

## Data Sources (All Free)

| Data | Source | Library/API |
|------|--------|-------------|
| Stock prices, market cap | Yahoo Finance | `yfinance` Python lib |
| Patent filings (US) | USPTO Patent API | REST API |
| Patent filings (EU) | EPO OPS API | REST API |
| SEC filings, funding | SEC EDGAR | REST API |
| Company descriptions | Wikipedia API | REST API |
| News headlines | NewsAPI.org | REST API (free: 100 req/day) |
| News sentiment | Claude API | ~$2-5/month |
| Insider trading | SEC EDGAR Form 4 | REST API |
| Institutional ownership | SEC EDGAR 13F | REST API |
| Government contracts | USASpending.gov | REST API |

## Companies Tracked

**Pure-play public quantum:**
- IonQ (IONQ), D-Wave Quantum (QBTS), Rigetti Computing (RGTI)
- Quantum Computing Inc (QUBT), Arqit Quantum (ARQQ)
- Infleqtion (INFQ), SEALSQ (LAES), BTQ Technologies (BTQ)
- QuantumCTek (688027.SS), Quantum eMotion (QNC.V), 01 Communique (ONE.V)

**Big tech with quantum divisions:**
- IBM, Google/Alphabet (GOOGL), Microsoft (MSFT)
- Amazon/AWS (AMZN), Intel (INTC), Honeywell/Quantinuum
- NVIDIA (NVDA), Fujitsu (6702.T)

**ETFs (ranked separately — scored by stock performance + sentiment only):**
- Defiance Quantum ETF (QTUM), WisdomTree Quantum Computing Fund (WQTM)
- VanEck Quantum Computing UCITS ETF (QNTM.L), iShares Quantum Computing UCITS ETF (QANT.AS)
- Global X AI Semiconductor & Quantum ETF (CHPX)

## Quantum Power Score Formula

### Companies
```
Quantum Power Score (0-100) =
  Stock momentum (20%)    → 30/60/90 day performance
  Patent velocity (25%)   → Patents filed last 12 months
  Qubit progress (20%)    → Latest announced qubit count
  Funding strength (20%)  → Total raised + recent rounds
  News sentiment (15%)    → AI-scored recent coverage
```

### ETFs
```
ETF Score (0-100) =
  Stock momentum (60%)    → 30/60/90 day performance
  News sentiment (40%)    → AI-scored recent coverage
```
ETFs don't have patents, qubits, or funding rounds, so they use a simplified
two-metric score and appear in a separate section on the leaderboard.

## Pages

1. **Main Leaderboard** (`/`) — Free. Sortable ranking table with Quantum Power Score, trend arrows, color coding.
2. **Company Detail** (`/company/:slug`) — Free. Stock chart, patent timeline, milestones, news feed, competitor comparison.
3. **Metric Deep Dives** (`/rankings/:metric`) — Free. One chart per metric, embeddable, shareable.
4. **Premium Dashboard** (`/pro`) — Paid ($9-19/month). Historical Power Score, full patent history, insider trading alerts, institutional ownership changes, R&D spend ratio, government contracts, CSV/JSON export, email alerts, API access, ad-free.

## Architecture Principles

- **Clean Architecture**: Separate domain logic from infrastructure. Use layers: domain → use cases → adapters → infrastructure.
- **TDD**: Write tests first. Every feature must have tests before implementation.
- **SOLID principles**: Single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion.
- **Separation of concerns**: Backend data pipeline is independent of frontend rendering.

## Project Structure (Target)

```
chartora/
├── backend/                    # FastAPI backend
│   ├── src/
│   │   ├── domain/             # Business entities, value objects
│   │   │   ├── models/         # Company, Score, Patent, Stock entities
│   │   │   └── interfaces/     # Repository & service interfaces (ports)
│   │   ├── usecases/           # Application business rules
│   │   │   ├── calculate_score.py
│   │   │   ├── fetch_stock_data.py
│   │   │   ├── fetch_patents.py
│   │   │   └── rank_companies.py
│   │   ├── adapters/           # Interface adapters
│   │   │   ├── api/            # FastAPI routes
│   │   │   └── repositories/   # DB implementations
│   │   ├── infrastructure/     # External services
│   │   │   ├── yahoo_finance.py
│   │   │   ├── uspto_client.py
│   │   │   ├── sec_edgar.py
│   │   │   ├── news_client.py
│   │   │   └── sentiment.py
│   │   └── config/             # Settings, env vars
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── scripts/                # Cron job scripts
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/                # Next.js app router pages
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── lib/                # Utilities, API client
│   │   └── types/              # TypeScript types
│   ├── tests/
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── infra/                      # Infrastructure configs
│   ├── nginx/
│   ├── docker-compose.yml
│   └── cron/
├── CLAUDE.md
├── ROADMAP.md
└── README.md
```

## Development Rules

### Mandatory Before Every Commit
1. **All tests must pass** — unit, integration, and e2e where applicable
2. **Linting must pass** — `ruff` for Python, `eslint` + `prettier` for TypeScript
3. **Type checking must pass** — `mypy` for Python, `tsc --noEmit` for TypeScript
4. **No secrets in code** — never commit API keys, tokens, or credentials
5. **Feature must be end-to-end complete** — no partial implementations committed

### TDD Workflow
1. Write a failing test that describes the desired behavior
2. Write the minimum code to make the test pass
3. Refactor while keeping tests green
4. Commit

### Code Style
- Python: Follow PEP 8, use type hints everywhere, use `ruff` for linting/formatting
- TypeScript: Strict mode, no `any` types, use ESLint + Prettier
- SQL: Use parameterized queries only — never string interpolation
- Commits: Conventional commits format (`feat:`, `fix:`, `test:`, `docs:`, `chore:`)

### Clean Architecture Rules
- Domain layer has ZERO external dependencies
- Use cases depend only on domain interfaces (ports), never on concrete implementations
- Infrastructure implements domain interfaces (adapters)
- Dependency injection for all external services
- No business logic in API routes or database repositories

## Monetization Strategy

| Phase | Timeline | Revenue Source | Estimated |
|-------|----------|---------------|-----------|
| 1 | Months 1-3 | Google AdSense | $50-75/month |
| 2 | Months 2-4 | Broker affiliate links | $50-200/month |
| 3 | Month 3+ | Premium tier ($9/month) | $450-1,800/month |
| 4 | Month 6+ | Sponsorships | $500-2,000/month |

## Monthly Costs

| Item | Cost |
|------|------|
| Hetzner CX22 | €4.49 |
| Claude API (sentiment) | ~$2-5 |
| Domain | ~$1/month amortized |
| **Total** | **~€8-11/month** |

## Key Commands

```bash
# Backend
cd backend && python -m pytest                    # Run all tests
cd backend && ruff check src/ tests/              # Lint Python
cd backend && mypy src/                           # Type check Python
cd backend && uvicorn src.adapters.api.main:app   # Run dev server

# Frontend
cd frontend && npm test                           # Run all tests
cd frontend && npm run lint                       # Lint TypeScript
cd frontend && npx tsc --noEmit                   # Type check
cd frontend && npm run dev                        # Run dev server

# Full stack
docker-compose up                                 # Run everything
```
