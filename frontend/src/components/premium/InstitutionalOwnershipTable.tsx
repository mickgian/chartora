"use client";

import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface InstitutionalFiling {
  filing_date: string;
  description: string | null;
  url: string | null;
  data: Record<string, unknown> | null;
}

interface InstitutionalOwnershipTableProps {
  slug: string;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function InstitutionalOwnershipTable({ slug }: InstitutionalOwnershipTableProps) {
  const [filings, setFilings] = useState<InstitutionalFiling[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);

    const token = localStorage.getItem("chartora_access_token");
    try {
      const res = await fetch(`${API_URL}/api/v1/pro/institutional-ownership/${slug}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Failed to load institutional ownership data");
      }
      const json = await res.json();
      setFilings(json.institutional_filings ?? []);
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
          Institutional Ownership (13F Filings)
        </h3>
        <p className="mt-1 text-xs text-gray-500 dark:text-slate-400">
          SEC 13F filings show which institutions hold positions in this company.
        </p>
      </div>

      {filings.length === 0 ? (
        <p className="p-4 text-sm text-gray-500 dark:text-slate-400">
          No institutional ownership filings found for this company. 13F data refreshes quarterly.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:border-gray-700 dark:text-slate-400">
                <th className="px-4 py-3">Filing Date</th>
                <th className="px-4 py-3">Institution / Description</th>
                <th className="px-4 py-3">Holdings</th>
                <th className="px-4 py-3">Link</th>
              </tr>
            </thead>
            <tbody>
              {filings.map((filing, i) => (
                <tr
                  key={`${filing.filing_date}-${i}`}
                  className="border-b border-gray-100 dark:border-gray-800 even:bg-gray-50 dark:even:bg-slate-800/30"
                >
                  <td className="whitespace-nowrap px-4 py-3 text-gray-900 dark:text-white">
                    {formatDate(filing.filing_date)}
                  </td>
                  <td className="px-4 py-3 text-gray-700 dark:text-slate-300">
                    {filing.data?.institution_name
                      ? String(filing.data.institution_name)
                      : filing.description ?? "13F Filing"}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-slate-400">
                    {filing.data ? (
                      <span className="text-xs">
                        {"shares_held" in filing.data && (
                          <span className="mr-2">{Number(filing.data.shares_held).toLocaleString()} shares</span>
                        )}
                        {"value" in filing.data && (
                          <span>
                            ${Number(filing.data.value).toLocaleString()}
                          </span>
                        )}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {filing.url ? (
                      <a
                        href={filing.url}
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
