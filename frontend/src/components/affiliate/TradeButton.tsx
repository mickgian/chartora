"use client";

import { getBrokers, buildTrackedAffiliateLink } from "@/lib/affiliate";

interface TradeButtonProps {
  ticker: string | null;
  companySlug: string;
  className?: string;
}

/**
 * "Trade [TICKER]" button with broker affiliate links.
 * Renders nothing if the company has no ticker.
 */
export function TradeButton({ ticker, companySlug, className = "" }: TradeButtonProps) {
  if (!ticker) return null;

  const brokers = getBrokers();

  return (
    <div className={`space-y-2 ${className}`} data-testid="trade-button">
      <p className="text-sm font-medium text-gray-700 dark:text-slate-300">
        Trade {ticker}
      </p>
      <div className="flex flex-wrap gap-2">
        {brokers.map((broker) => (
          <a
            key={broker.slug}
            href={buildTrackedAffiliateLink(broker.slug, ticker, companySlug)}
            target="_blank"
            rel="noopener noreferrer sponsored"
            className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm font-medium text-indigo-700 transition-colors hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-300 dark:hover:bg-indigo-950/60"
            data-testid={`trade-link-${broker.slug}`}
          >
            Trade on {broker.name}
          </a>
        ))}
      </div>
      <p className="text-[10px] text-gray-400 dark:text-gray-500">
        Affiliate links — we may earn a commission at no extra cost to you.
      </p>
    </div>
  );
}
