"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface HistoricalScore {
  date: string;
  total_score: number;
  stock_momentum: number;
  patent_velocity: number;
  qubit_progress: number;
  funding_strength: number;
  news_sentiment: number;
  rank: number | null;
}

interface SubMetric {
  key: keyof HistoricalScore;
  label: string;
  color: string;
}

const SUB_METRICS: SubMetric[] = [
  { key: "stock_momentum", label: "Stock Momentum", color: "#10b981" },
  { key: "patent_velocity", label: "Patent Velocity", color: "#8b5cf6" },
  { key: "qubit_progress", label: "Qubit Progress", color: "#f59e0b" },
  { key: "funding_strength", label: "Funding Strength", color: "#3b82f6" },
  { key: "news_sentiment", label: "News Sentiment", color: "#ef4444" },
];

interface HistoricalScoreChartProps {
  slug: string;
  period: number;
}

export function HistoricalScoreChart({ slug, period }: HistoricalScoreChartProps) {
  const [scores, setScores] = useState<HistoricalScore[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeMetrics, setActiveMetrics] = useState<Set<string>>(new Set());
  const [showRank, setShowRank] = useState(false);

  const fetchScores = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);

    const token = localStorage.getItem("chartora_access_token");
    try {
      const res = await fetch(
        `${API_URL}/api/v1/pro/historical-scores/${slug}?days=${period}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Failed to load data");
      }

      const data = await res.json();
      setScores(data.scores ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [slug, period]);

  useEffect(() => {
    fetchScores();
  }, [fetchScores]);

  function toggleMetric(key: string) {
    setActiveMetrics((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  return (
    <div className="space-y-4">
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

      {/* Sub-metric toggles */}
      <div className="flex flex-wrap gap-2">
        {SUB_METRICS.map((m) => (
          <button
            key={m.key}
            onClick={() => toggleMetric(m.key)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              activeMetrics.has(m.key)
                ? "border-transparent text-white"
                : "border-gray-300 text-gray-500 hover:border-gray-400 dark:border-gray-600 dark:text-slate-400"
            }`}
            style={activeMetrics.has(m.key) ? { backgroundColor: m.color } : undefined}
          >
            {m.label}
          </button>
        ))}
        <button
          onClick={() => setShowRank(!showRank)}
          className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
            showRank
              ? "border-transparent bg-gray-700 text-white dark:bg-gray-300 dark:text-gray-900"
              : "border-gray-300 text-gray-500 hover:border-gray-400 dark:border-gray-600 dark:text-slate-400"
          }`}
        >
          Rank
        </button>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
        </div>
      ) : scores.length > 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-slate-900">
          <h3 className="mb-4 text-sm font-semibold text-gray-700 dark:text-slate-300">
            Quantum Power Score History
          </h3>
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={scores}>
              <defs>
                <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                {SUB_METRICS.map((m) => (
                  <linearGradient key={m.key} id={`grad-${m.key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={m.color} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={m.color} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={"#374151"} opacity={0.5} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#d1d5db" }}
                tickFormatter={(v: string) => new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                stroke={"#4b5563"}
              />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#d1d5db" }} stroke={"#4b5563"} yAxisId="score" />
              {showRank && (
                <YAxis
                  yAxisId="rank"
                  orientation="right"
                  reversed
                  tick={{ fontSize: 11, fill: "#9ca3af" }}
                  stroke={"#6b7280"}
                  label={{ value: "Rank", angle: 90, position: "insideRight", style: { fontSize: 11, fill: "#9ca3af" } }}
                />
              )}
              <Tooltip
                contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #4b5563", borderRadius: "8px", fontSize: "12px", color: "#f3f4f6" }}
                itemStyle={{ color: "#f3f4f6" }}
                labelStyle={{ color: "#ffffff", fontWeight: 600 }}
                labelFormatter={(v) => new Date(String(v)).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
              />
              <Area
                type="monotone"
                dataKey="total_score"
                stroke="#6366f1"
                fill="url(#scoreGrad)"
                strokeWidth={2}
                name="Total Score"
                yAxisId="score"
              />
              {SUB_METRICS.filter((m) => activeMetrics.has(m.key)).map((m) => (
                <Area
                  key={m.key}
                  type="monotone"
                  dataKey={m.key}
                  stroke={m.color}
                  fill={`url(#grad-${m.key})`}
                  strokeWidth={1.5}
                  name={m.label}
                  yAxisId="score"
                />
              ))}
              {showRank && (
                <Line
                  type="monotone"
                  dataKey="rank"
                  stroke="#9ca3af"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  dot={false}
                  name="Rank"
                  yAxisId="rank"
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="py-8 text-center text-sm text-gray-500">No historical data available yet.</p>
      )}
    </div>
  );
}
