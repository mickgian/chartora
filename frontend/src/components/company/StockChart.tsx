"use client";

import { useCallback, useState } from "react";
import { useTheme } from "@/components/layout/ThemeProvider";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { IntradayResponse, StockHistoryResponse } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { useApi } from "@/hooks/use-api";
import { ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

function ytdDays(): number {
  const now = new Date();
  const jan1 = new Date(now.getFullYear(), 0, 1);
  return Math.ceil((now.getTime() - jan1.getTime()) / 86_400_000);
}

const PERIOD_OPTIONS = [
  { label: "1D", days: 1 },
  { label: "5D", days: 5 },
  { label: "1M", days: 30 },
  { label: "6M", days: 180 },
  { label: "YTD", days: ytdDays() },
  { label: "1Y", days: 365 },
  { label: "5Y", days: 1825 },
];

interface StockChartProps {
  slug: string;
}

interface ChartPoint {
  label: string;
  price: number;
}

function formatDateForRange(dateStr: string, days: number): string {
  const date = new Date(dateStr);
  if (days > 0 && days <= 90) {
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }
  if (days > 90 && days <= 365) {
    const month = date.toLocaleDateString("en-US", { month: "short" });
    const year = String(date.getFullYear()).slice(2);
    return `${month} '${year}`;
  }
  // 5Y or days>365
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

function formatTooltipDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function IntradayChart({ slug, isDark }: { slug: string; isDark: boolean }) {
  const fetcher = useCallback(() => apiClient.getIntradayHistory(slug), [slug]);
  const { data, error, loading, refetch } = useApi<IntradayResponse>(fetcher, [slug]);

  if (loading) return <ChartSkeleton />;
  if (error) return <ErrorMessage message={error.message} onRetry={refetch} />;
  if (!data || data.prices.length < 2) {
    // Not enough intraday data (market closed, off-hours) — fall back to 5-day daily chart
    return <DailyChart slug={slug} days={5} isDark={isDark} />;
  }

  const chartData: ChartPoint[] = data.prices.map((p) => ({
    label: p.timestamp,
    price: p.price,
  }));

  const prices = chartData.map((d) => d.price);
  const minPrice = Math.floor(Math.min(...prices) * 0.995);
  const maxPrice = Math.ceil(Math.max(...prices) * 1.005);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="stockGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#374151" : "#e5e7eb"} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 12, fill: isDark ? "#d1d5db" : "#6b7280" }}
          tickFormatter={(v: string) =>
            new Date(v).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
          }
          stroke={isDark ? "#4b5563" : "#d1d5db"}
        />
        <YAxis
          domain={[minPrice, maxPrice]}
          tick={{ fontSize: 12, fill: isDark ? "#d1d5db" : "#6b7280" }}
          stroke={isDark ? "#4b5563" : "#d1d5db"}
        />
        <Tooltip
          labelFormatter={(v) =>
            new Date(String(v)).toLocaleTimeString("en-US", {
              hour: "numeric",
              minute: "2-digit",
            })
          }
          formatter={(value) => [`$${Number(value).toFixed(2)}`, "Price"]}
          contentStyle={isDark ? { backgroundColor: "#1f2937", border: "1px solid #4b5563", borderRadius: "8px", color: "#f3f4f6" } : undefined}
          itemStyle={isDark ? { color: "#f3f4f6" } : undefined}
          labelStyle={isDark ? { color: "#ffffff", fontWeight: 600 } : undefined}
        />
        <Area
          type="monotone"
          dataKey="price"
          stroke="#6366f1"
          fill="url(#stockGradient)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function DailyChart({ slug, days, isDark }: { slug: string; days: number; isDark: boolean }) {
  const fetcher = useCallback(() => apiClient.getStockHistory(slug, days), [slug, days]);
  const { data, error, loading, refetch } = useApi<StockHistoryResponse>(fetcher, [slug, days]);

  if (loading) return <ChartSkeleton />;
  if (error) return <ErrorMessage message={error.message} onRetry={refetch} />;
  if (!data || data.prices.length === 0) {
    return <p className="text-sm text-gray-500 dark:text-slate-400">No stock data available.</p>;
  }

  const chartData: ChartPoint[] = data.prices.map((p) => ({
    label: p.price_date,
    price: p.close_price,
  }));

  const prices = chartData.map((d) => d.price);
  const minPrice = Math.floor(Math.min(...prices) * 0.95);
  const maxPrice = Math.ceil(Math.max(...prices) * 1.05);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="stockGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#374151" : "#e5e7eb"} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 12, fill: isDark ? "#d1d5db" : "#6b7280" }}
          tickFormatter={(v: string) => formatDateForRange(v, days)}
          minTickGap={days > 365 || days === 0 ? 50 : 30}
          stroke={isDark ? "#4b5563" : "#d1d5db"}
        />
        <YAxis domain={[minPrice, maxPrice]} tick={{ fontSize: 12, fill: isDark ? "#d1d5db" : "#6b7280" }} stroke={isDark ? "#4b5563" : "#d1d5db"} />
        <Tooltip
          labelFormatter={(v) => formatTooltipDate(String(v))}
          formatter={(value) => [`$${Number(value).toFixed(2)}`, "Price"]}
          contentStyle={isDark ? { backgroundColor: "#1f2937", border: "1px solid #4b5563", borderRadius: "8px", color: "#f3f4f6" } : undefined}
          itemStyle={isDark ? { color: "#f3f4f6" } : undefined}
          labelStyle={isDark ? { color: "#ffffff", fontWeight: 600 } : undefined}
        />
        <Area
          type="monotone"
          dataKey="price"
          stroke="#6366f1"
          fill="url(#stockGradient)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function StockChart({ slug }: StockChartProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [days, setDays] = useState(365);

  const isIntraday = days === 1;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Stock Price</h2>
        <div className="flex gap-1">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.label}
              onClick={() => setDays(opt.days)}
              className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                days === opt.days
                  ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300"
                  : "text-gray-500 hover:bg-gray-100 dark:text-slate-400 dark:hover:bg-slate-800"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {isIntraday ? (
        <IntradayChart slug={slug} isDark={isDark} />
      ) : (
        <DailyChart slug={slug} days={days} isDark={isDark} />
      )}
    </div>
  );
}
