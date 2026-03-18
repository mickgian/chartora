# ADR-001: Funding Data Sources — SEC EDGAR over Crunchbase/PitchBook

**Status:** Accepted
**Date:** 2026-03-18
**Decision makers:** Project maintainers

## Context

Chartora needs real-time funding data for quantum computing companies to calculate the "funding strength" component (20% weight) of the Quantum Power Score. Previously, funding amounts were hardcoded in a `KNOWN_FUNDING_USD` dictionary that required manual updates and went stale quickly.

We evaluated three categories of data sources:

### Option A: Crunchbase API

- **Pros:** Rich funding round data (series, investors, amounts), widely used by VCs
- **Cons:** Free tier provides only basic firmographic data. Funding round details require paid plans starting at $29/user/month, with full API access at enterprise/custom pricing
- **Verdict:** Too expensive for Chartora's ~$8-11/month operating budget

### Option B: PitchBook

- **Pros:** Comprehensive private market data, institutional-grade
- **Cons:** No public API. Enterprise pricing starts at $12,000-70,000+/year
- **Verdict:** Completely out of scope for this project

### Option C: SEC EDGAR (free, already partially integrated)

- **XBRL CompanyFacts API:** Stockholders' equity and total assets from 10-K/10-Q filings — already implemented via `SecEdgarXbrlAdapter`
- **Form D filings:** Private placement / Reg D exempt securities offerings — captures actual fundraising rounds with `totalAmountSold` and `totalOfferingAmount` fields
- **8-K filings:** Material events including funding announcements — already captured by existing `SecEdgarAdapter`
- **Pros:** Completely free, legally mandated disclosures, auto-updates daily via cron
- **Cons:** Only covers SEC-registered companies (covers all our tracked companies). Form D data may lag 15 days after first sale. Big tech companies (IBM, Google, etc.) don't file Form D since they don't do private placements — but their funding strength is captured via XBRL equity data

## Decision

Use SEC EDGAR as the sole funding data source, combining:

1. **XBRL CompanyFacts** (`SecEdgarXbrlAdapter.fetch_total_funding`) — stockholders' equity or total assets as a proxy for financial strength. Best for established/big tech companies.
2. **Form D filings** (`SecEdgarAdapter.fetch_form_d_total_raised`) — actual private placement amounts. Best for pure-play quantum startups that raise capital through Reg D offerings.
3. **Government contracts** (`UsaSpendingAdapter`) — already integrated, adds to total funding.

The score calculator takes `max(XBRL equity, Form D total raised) + government contracts`.

## Consequences

### Positive

- Zero additional cost — stays within the ~$8-11/month budget
- Auto-updating — daily cron pulls fresh data from SEC
- Legally mandated data — companies are required to file, so data is reliable
- Eliminates hardcoded `KNOWN_FUNDING_USD` dictionary that required manual maintenance

### Negative

- No coverage for non-US private companies (not currently tracked)
- Form D filings can lag up to 15 days after first sale
- XBRL equity is a proxy, not exact "total raised" — but for established companies, equity is a more meaningful measure of financial strength anyway

### Risks

- SEC EDGAR API rate limits (10 requests/second) — mitigated by sequential processing in cron job
- XBRL data schema changes — low risk, GAAP concepts are stable

## Alternatives Considered but Rejected

| Source | Why Rejected |
|--------|-------------|
| Crunchbase API | $29+/month for funding data, exceeds budget |
| PitchBook | $12K-70K/year, no public API |
| OpenCorporates | Limited financial data, primarily company registry info |
| Manual updates | Not scalable, goes stale, defeats auto-updating goal |

## References

- SEC EDGAR XBRL API: https://www.sec.gov/search#/dateRange=custom&forms=D
- SEC Form D overview: https://www.sec.gov/about/forms/formd.htm
- SEC EDGAR rate limits: https://www.sec.gov/os/accessing-edgar-data
