"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import type { LeaderboardEntry, LeaderboardResponse } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { useApi } from "@/hooks/use-api";
import { TableSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { ScoreBadge } from "./ScoreBadge";
import { TrendArrow } from "./TrendArrow";

type ETFSortMetric = "total_score" | "stock_momentum" | "news_sentiment";

const METRIC_LABELS: Record<ETFSortMetric, string> = {
  total_score: "Score",
  stock_momentum: "Stock %",
  news_sentiment: "Sentiment",
};

const SORTABLE_METRICS: ETFSortMetric[] = [
  "total_score",
  "stock_momentum",
  "news_sentiment",
];

const METRIC_SCORE_KEYS: Record<Exclude<ETFSortMetric, "total_score">, keyof LeaderboardEntry["score"]> = {
  stock_momentum: "stock_momentum",
  news_sentiment: "news_sentiment",
};

export function ETFLeaderboardTable() {
  const [sortBy, setSortBy] = useState<ETFSortMetric>("total_score");

  const fetcher = useCallback(
    () => apiClient.getLeaderboard({ sort_by: sortBy, sector: "etf" }),
    [sortBy],
  );
  const { data, error, loading, refetch } = useApi<LeaderboardResponse>(fetcher, [sortBy]);

  if (loading) return <TableSkeleton rows={5} />;
  if (error) return <ErrorMessage message={error.message} onRetry={refetch} />;
  if (!data || data.entries.length === 0) return null;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-bold text-gray-900 dark:text-slate-50">Quantum ETFs</h2>
        <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
          Scored by stock performance &amp; sentiment only
        </span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-slate-700">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-slate-700 dark:bg-slate-800/80">
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-slate-300">Rank</th>
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-slate-300">ETF</th>
              {SORTABLE_METRICS.map((metric) => (
                <th key={metric} className="px-4 py-3">
                  <button
                    onClick={() => setSortBy(metric)}
                    className={`font-medium transition-colors ${
                      sortBy === metric
                        ? "text-indigo-600 dark:text-indigo-300"
                        : "text-gray-500 hover:text-gray-700 dark:text-slate-300 dark:hover:text-slate-100"
                    }`}
                  >
                    {METRIC_LABELS[metric]}
                    {sortBy === metric && " \u2193"}
                  </button>
                </th>
              ))}
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-slate-300">Trend</th>
            </tr>
          </thead>
          <tbody>
            {data.entries.map((entry) => (
              <tr
                key={entry.company.slug}
                className="border-b border-gray-100 transition-colors hover:bg-gray-50 dark:border-slate-700/70 dark:hover:bg-slate-800/60"
              >
                <td className="px-4 py-3 font-bold text-gray-900 dark:text-slate-100">{entry.rank}</td>
                <td className="px-4 py-3">
                  <Link
                    href={`/company/${entry.company.slug}`}
                    className="font-medium text-gray-900 hover:text-indigo-600 dark:text-slate-100 dark:hover:text-indigo-300"
                  >
                    {entry.company.name}
                    {entry.company.ticker && (
                      <span className="ml-2 text-xs text-gray-500 dark:text-slate-400">
                        {entry.company.ticker}
                      </span>
                    )}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <ScoreBadge score={entry.score.total_score} />
                </td>
                {(Object.keys(METRIC_SCORE_KEYS) as Array<keyof typeof METRIC_SCORE_KEYS>).map((metric) => {
                  const key = METRIC_SCORE_KEYS[metric];
                  const value = entry.score[key];
                  return (
                    <td key={metric} className="px-4 py-3 tabular-nums text-gray-700 dark:text-slate-200">
                      {(value as number).toFixed(1)}
                    </td>
                  );
                })}
                <td className="px-4 py-3">
                  <TrendArrow trend={entry.trend} rankChange={entry.score.rank_change} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-3 text-xs text-gray-400 dark:text-slate-400">
        {data.entries.length} ETFs tracked. Click column headers to sort.
      </p>
    </div>
  );
}
