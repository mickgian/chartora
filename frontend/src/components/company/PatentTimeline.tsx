"use client";

import { useCallback } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PatentListResponse } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { useApi } from "@/hooks/use-api";
import { useTheme } from "@/components/layout/ThemeProvider";
import { ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

interface PatentTimelineProps {
  slug: string;
}

export function PatentTimeline({ slug }: PatentTimelineProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";
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
          <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#374151" : "#e5e7eb"} />
          <XAxis dataKey="month" tick={{ fontSize: 11, fill: isDark ? "#d1d5db" : "#6b7280" }} stroke={isDark ? "#4b5563" : "#d1d5db"} />
          <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: isDark ? "#d1d5db" : "#6b7280" }} stroke={isDark ? "#4b5563" : "#d1d5db"} />
          <Tooltip contentStyle={isDark ? { backgroundColor: "#1f2937", border: "1px solid #4b5563", borderRadius: "8px", color: "#f3f4f6" } : undefined} />
          <Bar dataKey="count" name="Patents Filed" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
