"use client";

import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface InsiderTrade {
  filing_date: string;
  description: string | null;
  url: string | null;
  data: Record<string, unknown> | null;
}

interface InsiderTradingTableProps {
  slug: string;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function InsiderTradingTable({ slug }: InsiderTradingTableProps) {
  const [trades, setTrades] = useState<InsiderTrade[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);

    const token = localStorage.getItem("chartora_access_token");
    try {
      const res = await fetch(`${API_URL}/api/v1/pro/insider-trading/${slug}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Failed to load insider trading data");
      }
      const json = await res.json();
      setTrades(json.insider_trades ?? []);
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
      <div className="flex h-32 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-red-600 dark:text-red-400">{error}</p>;
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-slate-900">
      <div className="border-b border-gray-200 p-4 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-300">
          Insider Trading (Form 4 Filings)
        </h3>
        <p className="mt-1 text-xs text-gray-500 dark:text-slate-400">
          SEC Form 4 filings reveal when company insiders buy or sell shares.
        </p>
      </div>

      {trades.length === 0 ? (
        <p className="p-4 text-sm text-gray-500 dark:text-slate-400">
          No insider trading filings found for this company. Form 4 data refreshes daily.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:border-gray-700 dark:text-slate-400">
                <th className="px-4 py-3">Filing Date</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Details</th>
                <th className="px-4 py-3">Link</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade, i) => (
                <tr
                  key={`${trade.filing_date}-${i}`}
                  className="border-b border-gray-100 dark:border-gray-800 even:bg-gray-50 dark:even:bg-slate-800/30"
                >
                  <td className="whitespace-nowrap px-4 py-3 text-gray-900 dark:text-white">
                    {formatDate(trade.filing_date)}
                  </td>
                  <td className="px-4 py-3 text-gray-700 dark:text-slate-300">
                    {trade.description ?? "Form 4 Filing"}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-slate-400">
                    {trade.data ? (
                      <span className="text-xs">
                        {"transaction_type" in trade.data && <span className="mr-2">{String(trade.data.transaction_type)}</span>}
                        {"shares" in trade.data && <span className="mr-2">{Number(trade.data.shares).toLocaleString()} shares</span>}
                        {"price_per_share" in trade.data && <span>@ ${Number(trade.data.price_per_share).toFixed(2)}</span>}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {trade.url ? (
                      <a
                        href={trade.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 hover:underline dark:text-indigo-400"
                      >
                        SEC Filing
                      </a>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
