"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
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

interface CompanyOption {
  slug: string;
  name: string;
}

const PERIOD_OPTIONS = [
  { value: 90, label: "90 days" },
  { value: 180, label: "6 months" },
  { value: 365, label: "1 year" },
];

export function HistoricalScoreChart() {
  const [companies, setCompanies] = useState<CompanyOption[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string>("");
  const [period, setPeriod] = useState(365);
  const [scores, setScores] = useState<HistoricalScore[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/leaderboard`)
      .then((res) => res.json())
      .then((data) => {
        const opts = data.entries?.map((e: { company: CompanyOption }) => ({
          slug: e.company.slug,
          name: e.company.name,
        })) ?? [];
        setCompanies(opts);
        if (opts.length > 0 && !selectedSlug) {
          setSelectedSlug(opts[0].slug);
        }
      })
      .catch(() => setCompanies([]));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchScores = useCallback(async () => {
    if (!selectedSlug) return;
    setLoading(true);
    setError(null);

    const token = localStorage.getItem("chartora_access_token");
    try {
      const res = await fetch(
        `${API_URL}/api/v1/pro/historical-scores/${selectedSlug}?days=${period}`,
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
  }, [selectedSlug, period]);

  useEffect(() => {
    fetchScores();
  }, [fetchScores]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <select
          value={selectedSlug}
          onChange={(e) => setSelectedSlug(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-white"
        >
          {companies.map((c) => (
            <option key={c.slug} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>

        <div className="flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPeriod(opt.value)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                period === opt.value
                  ? "bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white"
                  : "text-gray-500 hover:text-gray-700 dark:text-gray-400"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
        </div>
      ) : scores.length > 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
          <h3 className="mb-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
            Quantum Power Score History
          </h3>
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={scores}>
              <defs>
                <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11 }}
                tickFormatter={(v: string) => new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
              />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ borderRadius: "8px", fontSize: "12px" }}
                labelFormatter={(v) => new Date(String(v)).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
              />
              <Area
                type="monotone"
                dataKey="total_score"
                stroke="#6366f1"
                fill="url(#scoreGrad)"
                strokeWidth={2}
                name="Total Score"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="py-8 text-center text-sm text-gray-500">No historical data available yet.</p>
      )}
    </div>
  );
}
