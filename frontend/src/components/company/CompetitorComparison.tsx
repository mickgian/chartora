"use client";

import Link from "next/link";
import { useCallback } from "react";
import type { LeaderboardResponse } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { useApi } from "@/hooks/use-api";
import { ScoreBadge } from "@/components/leaderboard/ScoreBadge";

interface CompetitorComparisonProps {
  currentSlug: string;
}

export function CompetitorComparison({ currentSlug }: CompetitorComparisonProps) {
  const fetcher = useCallback(() => apiClient.getLeaderboard({ limit: 10 }), []);
  const { data, loading } = useApi<LeaderboardResponse>(fetcher, []);

  if (loading || !data) return null;

  const competitors = data.entries.filter((e) => e.company.slug !== currentSlug).slice(0, 5);

  if (competitors.length === 0) return null;

  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Top Competitors</h2>
      <div className="space-y-2">
        {competitors.map((entry) => (
          <Link
            key={entry.company.slug}
            href={`/company/${entry.company.slug}`}
            className="flex items-center justify-between rounded-lg border border-gray-200 p-3 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/50"
          >
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold text-gray-400 dark:text-gray-500">
                #{entry.rank}
              </span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {entry.company.name}
              </span>
            </div>
            <ScoreBadge score={entry.score.total_score} />
          </Link>
        ))}
      </div>
    </div>
  );
}
