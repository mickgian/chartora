"use client";

import Link from "next/link";
import { useCallback } from "react";
import type { CompanyDetailResponse } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { useApi } from "@/hooks/use-api";
import { CardSkeleton, ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { ScoreBadge } from "@/components/leaderboard/ScoreBadge";
import { AdSlot } from "@/components/ads/AdSlot";
import { TradeButton } from "@/components/affiliate/TradeButton";
import { StockChart } from "./StockChart";
import { PatentTimeline } from "./PatentTimeline";
import { NewsFeed } from "./NewsFeed";
import { CompetitorComparison } from "./CompetitorComparison";

interface CompanyDetailProps {
  slug: string;
}

const METRIC_LABELS: Record<string, string> = {
  stock_momentum: "Stock Momentum",
  patent_velocity: "Patent Velocity",
  qubit_progress: "Qubit Progress",
  funding_strength: "Funding Strength",
  news_sentiment: "News Sentiment",
};

export function CompanyDetail({ slug }: CompanyDetailProps) {
  const fetcher = useCallback(() => apiClient.getCompany(slug), [slug]);
  const { data, error, loading, refetch } = useApi<CompanyDetailResponse>(fetcher, [slug]);

  if (loading) {
    return (
      <div className="space-y-6">
        <CardSkeleton />
        <ChartSkeleton />
        <ChartSkeleton />
      </div>
    );
  }
  if (error) return <ErrorMessage message={error.message} onRetry={refetch} />;
  if (!data) return null;

  const { company, score } = data;

  return (
    <div>
      <nav className="mb-4 text-sm text-gray-500 dark:text-gray-400">
        <Link href="/" className="hover:text-gray-700 dark:hover:text-gray-300">
          Leaderboard
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900 dark:text-white">{company.name}</span>
      </nav>

      <div className="mb-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{company.name}</h1>
            <div className="mt-1 flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
              {company.ticker && (
                <span className="rounded bg-gray-100 px-2 py-0.5 font-mono font-medium dark:bg-gray-800">
                  {company.ticker}
                </span>
              )}
              <span className="capitalize">{company.sector.replace("_", " ")}</span>
              {company.is_etf && (
                <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                  ETF
                </span>
              )}
            </div>
          </div>
          {score && <ScoreBadge score={score.total_score} />}
        </div>

        {company.description && (
          <p className="mt-4 text-sm leading-relaxed text-gray-600 dark:text-gray-400">
            {company.description}
          </p>
        )}
      </div>

      {score && (
        <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-5">
          {Object.entries(METRIC_LABELS).map(([key, label]) => (
            <div key={key} className="rounded-lg border border-gray-200 p-3 dark:border-gray-800">
              <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
              <div className="mt-1 text-lg font-bold text-gray-900 dark:text-white">
                {(score[key as keyof typeof score] as number).toFixed(1)}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="space-y-8 lg:col-span-2">
          <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
            <StockChart slug={slug} />
          </div>
          <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
            <PatentTimeline slug={slug} />
          </div>
          <AdSlot adSlot="company-between" placement="between-sections" />
          <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
            <NewsFeed slug={slug} />
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
            <CompetitorComparison currentSlug={slug} />
          </div>
          <TradeButton ticker={company.ticker} companySlug={company.slug} />
          <AdSlot adSlot="company-sidebar" placement="sidebar" />
          {company.website && (
            <a
              href={company.website}
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-lg border border-gray-200 p-4 text-center text-sm font-medium text-indigo-600 transition-colors hover:bg-indigo-50 dark:border-gray-800 dark:text-indigo-400 dark:hover:bg-indigo-950/30"
            >
              Visit Company Website
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
