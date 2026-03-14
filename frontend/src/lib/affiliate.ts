/**
 * Affiliate link generation and broker configuration.
 * Generates tracked affiliate links for stock broker partners.
 */

export interface BrokerConfig {
  name: string;
  slug: string;
  baseUrl: string;
  /** Template for the affiliate URL. {ticker} is replaced with the company ticker. */
  urlTemplate: string;
  logo?: string;
}

const BROKERS: BrokerConfig[] = [
  {
    name: "Interactive Brokers",
    slug: "ibkr",
    baseUrl: "https://www.interactivebrokers.com",
    urlTemplate:
      "https://www.interactivebrokers.com/mkt/?src=chartora&conid={ticker}",
  },
  {
    name: "eToro",
    slug: "etoro",
    baseUrl: "https://www.etoro.com",
    urlTemplate:
      "https://www.etoro.com/markets/{ticker}?utm_source=chartora&utm_medium=affiliate",
  },
];

export function getBrokers(): BrokerConfig[] {
  return BROKERS;
}

/**
 * Generate an affiliate link for a specific broker and ticker.
 * Returns null if the company has no ticker.
 */
export function generateAffiliateLink(
  broker: BrokerConfig,
  ticker: string | null,
): string | null {
  if (!ticker) return null;
  return broker.urlTemplate.replace("{ticker}", encodeURIComponent(ticker));
}

/**
 * Build a tracking URL that routes through our click tracker.
 */
export function buildTrackedAffiliateLink(
  brokerSlug: string,
  ticker: string,
  companySlug: string,
): string {
  const params = new URLSearchParams({
    broker: brokerSlug,
    ticker,
    company: companySlug,
  });
  return `/api/affiliate/click?${params.toString()}`;
}
