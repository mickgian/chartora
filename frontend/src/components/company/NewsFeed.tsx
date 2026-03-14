"use client";

import { useCallback } from "react";
import type { NewsListResponse } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { useApi } from "@/hooks/use-api";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

interface NewsFeedProps {
  slug: string;
}

function SentimentBadge({ sentiment }: { sentiment: string | null }) {
  if (!sentiment) return null;
  const colors: Record<string, string> = {
    bullish: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
    bearish: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
    neutral: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
  };
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors[sentiment] ?? colors.neutral}`}
    >
      {sentiment}
    </span>
  );
}

export function NewsFeed({ slug }: NewsFeedProps) {
  const fetcher = useCallback(() => apiClient.getNews(slug), [slug]);
  const { data, error, loading, refetch } = useApi<NewsListResponse>(fetcher, [slug]);

  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-16 rounded bg-gray-100 dark:bg-gray-800/50" />
        ))}
      </div>
    );
  }
  if (error) return <ErrorMessage message={error.message} onRetry={refetch} />;
  if (!data || data.articles.length === 0) {
    return <p className="text-sm text-gray-500 dark:text-gray-400">No recent news.</p>;
  }

  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Recent News</h2>
      <ul className="space-y-3">
        {data.articles.map((article, i) => (
          <li
            key={i}
            className="rounded-lg border border-gray-200 p-4 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/50"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-gray-900 hover:text-indigo-600 dark:text-white dark:hover:text-indigo-400"
                >
                  {article.title}
                </a>
                <div className="mt-1 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                  {article.source_name && <span>{article.source_name}</span>}
                  <span>{new Date(article.published_at).toLocaleDateString()}</span>
                </div>
              </div>
              <SentimentBadge sentiment={article.sentiment} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
