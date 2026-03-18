"use client";

import Link from "next/link";
import { useCallback } from "react";
import type { RankingMetric, RankingResponse } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { useApi } from "@/hooks/use-api";
import { TableSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { TrendArrow } from "@/components/leaderboard/TrendArrow";
import { MetricChart } from "./MetricChart";

interface MetricInfo {
  title: string;
  label: string;
  description: string;
  sources: string[];
  calculation: string;
}

const METRIC_DETAILS: Record<RankingMetric, MetricInfo> = {
  "stock-performance": {
    title: "Stock Performance Rankings",
    label: "Stock Momentum",
    description: "Companies ranked by blended 30/60/90-day stock returns.",
    sources: [
      "Daily closing prices, market cap, and historical returns",
    ],
    calculation: "Weighted average of 30-day (40%), 60-day (35%), and 90-day (25%) returns, normalized 0-100.",
  },
  patents: {
    title: "Patent Activity Rankings",
    label: "Patent Velocity",
    description: "Companies ranked by patent filings in the last 12 months.",
    sources: [
      "US patent applications and grants",
      "European patent filings",
    ],
    calculation: "Total patents filed in the trailing 12-month window, normalized against the highest filer.",
  },
  funding: {
    title: "Funding Rankings",
    label: "Funding Strength",
    description: "Companies ranked by financial strength using regulatory filings — the same mandatory disclosures institutional investors rely on.",
    sources: [
      "Stockholders' equity or total assets from 10-K (annual) and 10-Q (quarterly) filings",
      "Private placement amounts from Regulation D exempt securities offerings",
      "Federal government contract awards and grant values",
    ],
    calculation: "max(stockholders' equity, total raised) + government contract value. Normalized: $0 = 0, $1B+ = 100. Blended 70% total funding, 30% most recent round.",
  },
  sentiment: {
    title: "News Sentiment Rankings",
    label: "News Sentiment",
    description: "Companies ranked by AI-scored news sentiment.",
    sources: [
      "Aggregated headlines from major financial and tech news outlets",
      "AI-powered sentiment scoring classifying each article as bullish, bearish, or neutral with a confidence score",
    ],
    calculation: "Average sentiment score across recent articles, weighted by recency. Bullish = positive, bearish = negative, normalized 0-100.",
  },
};

interface MetricDeepDiveProps {
  metric: RankingMetric;
}

export function MetricDeepDive({ metric }: MetricDeepDiveProps) {
  const details = METRIC_DETAILS[metric];
  const fetcher = useCallback(() => apiClient.getRanking(metric), [metric]);
  const { data, error, loading, refetch } = useApi<RankingResponse>(fetcher, [metric]);

  if (loading) return <TableSkeleton rows={12} />;
  if (error) return <ErrorMessage message={error.message} onRetry={refetch} />;
  if (!data) return null;

  const isEmpty = data.entries.length === 0;

  return (
    <div>
      <nav className="mb-4 text-sm text-gray-500 dark:text-slate-400">
        <Link href="/" className="hover:text-gray-700 dark:hover:text-slate-300">
          Leaderboard
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900 dark:text-white">{details.title}</span>
      </nav>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{details.title}</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">{details.description}</p>
      </div>

      {/* Data source transparency */}
      <div className="mb-8 rounded-lg border border-gray-200 bg-gray-50 p-5 dark:border-gray-700 dark:bg-slate-800/50">
        <div className="mb-3 flex items-center gap-2">
          <svg className="h-4 w-4 text-gray-500 dark:text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-300">How this ranking is calculated</h3>
        </div>
        <p className="mb-3 text-sm text-gray-600 dark:text-slate-400">{details.calculation}</p>
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-400">
          Data sources
        </div>
        <ul className="space-y-1.5">
          {details.sources.map((source) => (
            <li key={source} className="flex items-start gap-2 text-sm">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-green-500" />
              <span className="text-gray-600 dark:text-slate-400">{source}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-gray-400 dark:text-slate-500">
          All data sourced from publicly accessible government and financial data.
          No manual overrides.{" "}
          <Link href="/methodology" className="text-indigo-500 underline hover:text-indigo-600 dark:text-indigo-400 dark:hover:text-indigo-300">
            Full methodology
          </Link>
        </p>
      </div>

      {isEmpty ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-8 text-center dark:border-amber-700/50 dark:bg-amber-900/20">
          <p className="text-lg font-medium text-amber-800 dark:text-amber-200">
            No {details.label.toLowerCase()} data available yet
          </p>
          <p className="mt-2 text-sm text-amber-600 dark:text-amber-300/80">
            The data refresh pipeline has not been run yet. Run the refresh script to populate
            ranking data.
          </p>
        </div>
      ) : (
      <>
      <div className="mb-8 rounded-lg border border-gray-200 p-6 dark:border-gray-700">
        <MetricChart entries={data.entries} metricLabel={details.label} />
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-slate-800/80">
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-slate-300">Rank</th>
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-slate-300">Company</th>
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-slate-300">
                {details.label}
              </th>
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-slate-300">Trend</th>
            </tr>
          </thead>
          <tbody>
            {data.entries.map((entry) => (
              <tr
                key={entry.company.slug}
                className="border-b border-gray-100 transition-colors hover:bg-gray-50 dark:border-slate-700/70 dark:hover:bg-slate-800/60"
              >
                <td className="px-4 py-3 font-bold text-gray-900 dark:text-white">{entry.rank}</td>
                <td className="px-4 py-3">
                  <Link
                    href={`/company/${entry.company.slug}`}
                    className="font-medium text-gray-900 hover:text-indigo-600 dark:text-white dark:hover:text-indigo-400"
                  >
                    {entry.company.name}
                    {entry.company.ticker && (
                      <span className="ml-2 text-xs text-gray-500 dark:text-slate-400">
                        {entry.company.ticker}
                      </span>
                    )}
                  </Link>
                </td>
                <td className="px-4 py-3 tabular-nums text-gray-700 dark:text-slate-300">
                  {entry.metric_value.toFixed(2)}
                </td>
                <td className="px-4 py-3">
                  <TrendArrow trend={entry.trend} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      </>
      )}

      <p className="mt-3 text-xs text-gray-400 dark:text-slate-400">
        {data.count} companies ranked by {details.label.toLowerCase()}.
      </p>
    </div>
  );
}
