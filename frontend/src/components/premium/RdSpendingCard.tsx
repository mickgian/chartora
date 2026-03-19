"use client";

import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface RdData {
  rd_expense: number | null;
  total_revenue: number | null;
  rd_ratio: number | null;
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(1)}B`;
  }
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function ratioColor(ratio: number): string {
  if (ratio >= 0.5) return "text-green-500";
  if (ratio >= 0.2) return "text-yellow-500";
  return "text-red-500";
}

interface RdSpendingCardProps {
  slug: string;
}

export function RdSpendingCard({ slug }: RdSpendingCardProps) {
  const [data, setData] = useState<RdData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);

    const token = localStorage.getItem("chartora_access_token");
    try {
      const res = await fetch(`${API_URL}/api/v1/pro/rd-spending/${slug}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Failed to load R&D data");
      }
      const json = await res.json();
      setData({ rd_expense: json.rd_expense, total_revenue: json.total_revenue, rd_ratio: json.rd_ratio });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex h-24 items-center justify-center rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-slate-900">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-600 dark:text-red-400">{error}</p>;
  }

  if (!data || (data.rd_expense === null && data.total_revenue === null && data.rd_ratio === null)) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-slate-900">
        <p className="text-sm text-gray-500 dark:text-slate-400">
          R&D spending data is not available for this company.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-slate-900">
      <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-slate-300">R&D Spending Analysis</h3>
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-xs text-gray-500 dark:text-slate-400">R&D Expense</p>
          <p className="mt-1 text-lg font-bold text-gray-900 dark:text-white">
            {data.rd_expense !== null ? formatCurrency(data.rd_expense) : "N/A"}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 dark:text-slate-400">Total Revenue</p>
          <p className="mt-1 text-lg font-bold text-gray-900 dark:text-white">
            {data.total_revenue !== null ? formatCurrency(data.total_revenue) : "N/A"}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 dark:text-slate-400">R&D Ratio</p>
          <p className={`mt-1 text-lg font-bold ${data.rd_ratio !== null ? ratioColor(data.rd_ratio) : "text-gray-900 dark:text-white"}`}>
            {data.rd_ratio !== null ? `${(data.rd_ratio * 100).toFixed(1)}%` : "N/A"}
          </p>
        </div>
      </div>
    </div>
  );
}
