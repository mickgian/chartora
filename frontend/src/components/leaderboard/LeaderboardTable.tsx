"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import type { LeaderboardEntry, LeaderboardResponse, SortableMetric } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { useApi } from "@/hooks/use-api";
import { TableSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { ScoreBadge } from "./ScoreBadge";
import { TrendArrow } from "./TrendArrow";

const METRIC_LABELS: Record<SortableMetric, string> = {
  total_score: "Score",
  stock_momentum: "Stock %",
  patent_velocity: "Patents",
  qubit_progress: "Qubits",
  funding_strength: "Funding",
  news_sentiment: "Sentiment",
};

const SORTABLE_METRICS: SortableMetric[] = [
  "total_score",
  "stock_momentum",
  "patent_velocity",
  "qubit_progress",
  "funding_strength",
  "news_sentiment",
];

const METRIC_SCORE_KEYS: Record<Exclude<SortableMetric, "total_score">, keyof LeaderboardEntry["score"]> = {
  stock_momentum: "stock_momentum",
  patent_velocity: "patent_velocity",
  qubit_progress: "qubit_progress",
  funding_strength: "funding_strength",
  news_sentiment: "news_sentiment",
};

export function LeaderboardTable() {
  const [sortBy, setSortBy] = useState<SortableMetric>("total_score");

  const fetcher = useCallback(() => apiClient.getLeaderboard({ sort_by: sortBy }), [sortBy]);
  const { data, error, loading, refetch } = useApi<LeaderboardResponse>(fetcher, [sortBy]);

  if (loading) return <TableSkeleton rows={12} />;
  if (error) return <ErrorMessage message={error.message} onRetry={refetch} />;
  if (!data) return null;

  const isEmpty = data.entries.length === 0;
  const hardcodedSet = new Set(data.hardcoded_metrics ?? []);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-50">Quantum Power Rankings</h1>
        {data.updated_at && (
          <span className="text-xs text-gray-500 dark:text-slate-300">
            Updated {new Date(data.updated_at).toLocaleDateString()}
          </span>
        )}
      </div>

      {isEmpty ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-8 text-center dark:border-amber-700/50 dark:bg-amber-900/20">
          <p className="text-lg font-medium text-amber-800 dark:text-amber-200">
            No ranking data available yet
          </p>
          <p className="mt-2 text-sm text-amber-600 dark:text-amber-300/80">
            The data refresh pipeline has not been run yet. Run the refresh script to populate
            company scores: <code className="rounded bg-amber-100 px-1.5 py-0.5 text-xs dark:bg-amber-800/40">python -m scripts.refresh_data</code>
          </p>
        </div>
      ) : (
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-slate-700">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-slate-700 dark:bg-slate-800/80">
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-slate-300">Rank</th>
              <th className="px-4 py-3 font-medium text-gray-500 dark:text-slate-300">Company</th>
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
                    {sortBy === metric && " ↓"}
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
                  const isHardcoded = hardcodedSet.has(metric);
                  return (
                    <td
                      key={metric}
                      className={`px-4 py-3 tabular-nums ${
                        isHardcoded
                          ? "text-red-500 dark:text-red-400"
                          : "text-gray-700 dark:text-slate-200"
                      }`}
                      title={isHardcoded ? "Hardcoded / estimated data" : undefined}
                    >
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
      )}

      <p className="mt-3 text-xs text-gray-400 dark:text-slate-400">
        {data.count} companies tracked.{!isEmpty && " Click column headers to sort."}
      </p>
    </div>
  );
}
