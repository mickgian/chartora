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

const METRIC_DETAILS: Record<RankingMetric, { title: string; label: string; description: string }> =
  {
    "stock-performance": {
      title: "Stock Performance Rankings",
      label: "Stock Momentum",
      description: "Companies ranked by blended 30/60/90-day stock returns.",
    },
    patents: {
      title: "Patent Activity Rankings",
      label: "Patent Velocity",
      description: "Companies ranked by patent filings in the last 12 months.",
    },
    funding: {
      title: "Funding Rankings",
      label: "Funding Strength",
      description: "Companies ranked by total funding raised and recent rounds.",
    },
    sentiment: {
      title: "News Sentiment Rankings",
      label: "News Sentiment",
      description: "Companies ranked by AI-scored news sentiment.",
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

  return (
    <div>
      <nav className="mb-4 text-sm text-gray-500 dark:text-gray-400">
        <Link href="/" className="hover:text-gray-700 dark:hover:text-gray-300">
          Leaderboard
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900 dark:text-white">{details.title}</span>
      </nav>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{details.title}</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{details.description}</p>
      </div>

      <div className="mb-8 rounded-lg border border-gray-200 p-6 dark:border-gray-800">
        <MetricChart entries={data.entries} metricLabel={details.label} />
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900">
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Rank</th>
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Company</th>
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">
                {details.label}
              </th>
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Trend</th>
            </tr>
          </thead>
          <tbody>
            {data.entries.map((entry) => (
              <tr
                key={entry.company.slug}
                className="border-b border-gray-100 transition-colors hover:bg-gray-50 dark:border-gray-800/50 dark:hover:bg-gray-900/50"
              >
                <td className="px-4 py-3 font-bold text-gray-900 dark:text-white">{entry.rank}</td>
                <td className="px-4 py-3">
                  <Link
                    href={`/company/${entry.company.slug}`}
                    className="font-medium text-gray-900 hover:text-indigo-600 dark:text-white dark:hover:text-indigo-400"
                  >
                    {entry.company.name}
                    {entry.company.ticker && (
                      <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                        {entry.company.ticker}
                      </span>
                    )}
                  </Link>
                </td>
                <td className="px-4 py-3 tabular-nums text-gray-700 dark:text-gray-300">
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

      <p className="mt-3 text-xs text-gray-400 dark:text-gray-500">
        {data.count} companies ranked by {details.label.toLowerCase()}.
      </p>
    </div>
  );
}
