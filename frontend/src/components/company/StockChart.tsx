"use client";

import { useCallback, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { StockHistoryResponse } from "@/types/api";
import { apiClient } from "@/lib/api-client";
import { useApi } from "@/hooks/use-api";
import { ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

const PERIOD_OPTIONS = [
  { label: "30D", days: 30 },
  { label: "90D", days: 90 },
  { label: "1Y", days: 365 },
] as const;

interface StockChartProps {
  slug: string;
}

export function StockChart({ slug }: StockChartProps) {
  const [days, setDays] = useState(90);

  const fetcher = useCallback(() => apiClient.getStockHistory(slug, days), [slug, days]);
  const { data, error, loading, refetch } = useApi<StockHistoryResponse>(fetcher, [slug, days]);

  if (loading) return <ChartSkeleton />;
  if (error) return <ErrorMessage message={error.message} onRetry={refetch} />;
  if (!data || data.prices.length === 0) {
    return <p className="text-sm text-gray-500 dark:text-gray-400">No stock data available.</p>;
  }

  const chartData = data.prices.map((p) => ({
    date: p.price_date,
    price: p.close_price,
  }));

  const prices = chartData.map((d) => d.price);
  const minPrice = Math.floor(Math.min(...prices) * 0.95);
  const maxPrice = Math.ceil(Math.max(...prices) * 1.05);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Stock Price</h2>
        <div className="flex gap-1">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.days}
              onClick={() => setDays(opt.days)}
              className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                days === opt.days
                  ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300"
                  : "text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="stockGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(v: string) =>
              new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric" })
            }
          />
          <YAxis domain={[minPrice, maxPrice]} tick={{ fontSize: 12 }} />
          <Tooltip
            labelFormatter={(v) => new Date(String(v)).toLocaleDateString()}
            formatter={(value) => [`$${Number(value).toFixed(2)}`, "Price"]}
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
    </div>
  );
}
