"use client";

import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Patent {
  patent_number: string;
  title: string;
  filing_date: string;
  grant_date: string | null;
  source: "USPTO" | "EPO";
  abstract: string | null;
  classification: string | null;
}

interface FullPatentHistoryProps {
  slug: string;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function FullPatentHistory({ slug }: FullPatentHistoryProps) {
  const [patents, setPatents] = useState<Patent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState<"all" | "USPTO" | "EPO">("all");
  const [search, setSearch] = useState("");

  const fetchData = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);

    const token = localStorage.getItem("chartora_access_token");
    try {
      const res = await fetch(`${API_URL}/api/v1/pro/patents/${slug}/full-history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Failed to load patent data");
      }
      const json = await res.json();
      setPatents(json.patents ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filtered = patents.filter((p) => {
    if (sourceFilter !== "all" && p.source !== sourceFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        p.title.toLowerCase().includes(q) ||
        p.patent_number.toLowerCase().includes(q) ||
        (p.abstract && p.abstract.toLowerCase().includes(q))
      );
    }
    return true;
  });

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
      <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-slate-900">
        <div className="border-b border-gray-200 p-4 dark:border-gray-700">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-300">
                Full Patent History
              </h3>
              <p className="mt-1 text-xs text-gray-500 dark:text-slate-400">
                {patents.length} patent{patents.length !== 1 ? "s" : ""} on record (USPTO + EPO)
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-slate-800/80">
                {(["all", "USPTO", "EPO"] as const).map((opt) => (
                  <button
                    key={opt}
                    onClick={() => setSourceFilter(opt)}
                    className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                      sourceFilter === opt
                        ? "bg-white text-gray-900 shadow-sm dark:bg-slate-700 dark:text-white"
                        : "text-gray-500 hover:text-gray-700 dark:text-slate-400"
                    }`}
                  >
                    {opt === "all" ? "All" : opt}
                  </button>
                ))}
              </div>
              <input
                type="text"
                placeholder="Search patents..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-1 text-xs dark:border-gray-700 dark:bg-slate-800/80 dark:text-white"
              />
            </div>
          </div>
        </div>

        {filtered.length === 0 ? (
          <p className="p-4 text-sm text-gray-500 dark:text-slate-400">
            {patents.length === 0
              ? "No patents found for this company."
              : "No patents match the current filter."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:border-gray-700 dark:text-slate-400">
                  <th className="px-4 py-3">Patent #</th>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Filed</th>
                  <th className="px-4 py-3">Granted</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Classification</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((patent) => (
                  <>
                    <tr
                      key={patent.patent_number}
                      className={`border-b border-gray-100 dark:border-gray-800 even:bg-gray-50 dark:even:bg-slate-800/30 ${patent.abstract ? "cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800/50" : ""}`}
                      onClick={() => patent.abstract && setExpandedId(expandedId === patent.patent_number ? null : patent.patent_number)}
                    >
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-gray-900 dark:text-white">
                        {patent.patent_number}
                      </td>
                      <td className="max-w-xs truncate px-4 py-3 text-gray-700 dark:text-slate-300">
                        {patent.title}
                        {patent.abstract && (
                          <span className="ml-1 text-xs text-indigo-500">{expandedId === patent.patent_number ? "[-]" : "[+]"}</span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-gray-600 dark:text-slate-400">
                        {formatDate(patent.filing_date)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-gray-600 dark:text-slate-400">
                        {patent.grant_date ? formatDate(patent.grant_date) : "Pending"}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          patent.source === "USPTO"
                            ? "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
                            : "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300"
                        }`}>
                          {patent.source}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500 dark:text-slate-400">
                        {patent.classification ?? "—"}
                      </td>
                    </tr>
                    {expandedId === patent.patent_number && patent.abstract && (
                      <tr key={`${patent.patent_number}-abstract`}>
                        <td colSpan={6} className="bg-gray-50 px-4 py-3 text-xs leading-relaxed text-gray-600 dark:bg-slate-800/50 dark:text-slate-400">
                          <span className="font-medium text-gray-700 dark:text-slate-300">Abstract: </span>
                          {patent.abstract}
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
