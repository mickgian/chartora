"use client";

import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Contract {
  award_id: string;
  title: string;
  amount: number;
  awarding_agency: string;
  start_date: string;
  end_date: string | null;
  description: string | null;
}

interface GovernmentContractsProps {
  slug: string;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

export function GovernmentContracts({ slug }: GovernmentContractsProps) {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [totalValue, setTotalValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);

    const token = localStorage.getItem("chartora_access_token");
    try {
      const res = await fetch(`${API_URL}/api/v1/pro/government-contracts/${slug}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Failed to load government contracts");
      }
      const json = await res.json();
      setContracts(json.contracts ?? []);
      setTotalValue(json.total_value ?? 0);
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
    <div className="space-y-4">
      {/* Total value summary */}
      {contracts.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-400">Total Government Contract Value</p>
              <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">{formatCurrency(totalValue)}</p>
            </div>
            <p className="text-sm text-gray-500 dark:text-slate-400">
              {contracts.length} contract{contracts.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-slate-900">
        <div className="border-b border-gray-200 p-4 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-300">
            Government Contracts (USASpending.gov)
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-slate-400">
            Federal contract awards sourced from USASpending.gov.
          </p>
        </div>

        {contracts.length === 0 ? (
          <p className="p-4 text-sm text-gray-500 dark:text-slate-400">
            No government contracts found for this company.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:border-gray-700 dark:text-slate-400">
                  <th className="px-4 py-3">Award ID</th>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Agency</th>
                  <th className="px-4 py-3">Start</th>
                  <th className="px-4 py-3">End</th>
                </tr>
              </thead>
              <tbody>
                {contracts.map((c) => (
                  <>
                    <tr
                      key={c.award_id}
                      className={`border-b border-gray-100 dark:border-gray-800 even:bg-gray-50 dark:even:bg-slate-800/30 ${c.description ? "cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800/50" : ""}`}
                      onClick={() => c.description && setExpandedId(expandedId === c.award_id ? null : c.award_id)}
                    >
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-gray-900 dark:text-white">
                        {c.award_id}
                      </td>
                      <td className="max-w-xs truncate px-4 py-3 text-gray-700 dark:text-slate-300">
                        {c.title}
                        {c.description && (
                          <span className="ml-1 text-xs text-indigo-500">{expandedId === c.award_id ? "[-]" : "[+]"}</span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900 dark:text-white">
                        {formatCurrency(c.amount)}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-slate-400">{c.awarding_agency}</td>
                      <td className="whitespace-nowrap px-4 py-3 text-gray-600 dark:text-slate-400">
                        {formatDate(c.start_date)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-gray-600 dark:text-slate-400">
                        {c.end_date ? formatDate(c.end_date) : "Ongoing"}
                      </td>
                    </tr>
                    {expandedId === c.award_id && c.description && (
                      <tr key={`${c.award_id}-desc`}>
                        <td colSpan={6} className="bg-gray-50 px-4 py-3 text-xs leading-relaxed text-gray-600 dark:bg-slate-800/50 dark:text-slate-400">
                          {c.description}
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
