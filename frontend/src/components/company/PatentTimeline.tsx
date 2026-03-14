"use client";

import { useCallback } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PatentListResponse } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { useApi } from "@/hooks/use-api";
import { ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

interface PatentTimelineProps {
  slug: string;
}

export function PatentTimeline({ slug }: PatentTimelineProps) {
  const fetcher = useCallback(() => apiClient.getPatents(slug), [slug]);
  const { data, error, loading, refetch } = useApi<PatentListResponse>(fetcher, [slug]);

  if (loading) return <ChartSkeleton />;
  if (error) return <ErrorMessage message={error.message} onRetry={refetch} />;
  if (!data || data.patents.length === 0) {
    return <p className="text-sm text-gray-500 dark:text-gray-400">No patent data available.</p>;
  }

  const monthCounts = new Map<string, number>();
  for (const patent of data.patents) {
    const month = patent.filing_date.slice(0, 7);
    monthCounts.set(month, (monthCounts.get(month) ?? 0) + 1);
  }

  const chartData = Array.from(monthCounts.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, count]) => ({ month, count }));

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Patent Filings</h2>
        <span className="text-sm text-gray-500 dark:text-gray-400">{data.count} total patents</span>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="month" tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey="count" name="Patents Filed" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
