"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getToken(): string {
  return localStorage.getItem("chartora_access_token") ?? "";
}

export function ExportButtons() {
  const [downloading, setDownloading] = useState<string | null>(null);

  async function handleExport(format: "csv" | "json") {
    setDownloading(format);
    try {
      const res = await fetch(`${API_URL}/api/v1/pro/export/${format}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });

      if (!res.ok) throw new Error("Export failed");

      if (format === "csv") {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `chartora-rankings.csv`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `chartora-rankings.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch {
      alert("Export failed. Please try again.");
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600 dark:text-slate-400">
        Download the current quantum computing company rankings data.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        <button
          onClick={() => handleExport("csv")}
          disabled={downloading === "csv"}
          className="flex items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white px-6 py-4 text-sm font-medium text-gray-900 transition-colors hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800"
        >
          <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {downloading === "csv" ? "Downloading..." : "Export CSV"}
        </button>

        <button
          onClick={() => handleExport("json")}
          disabled={downloading === "json"}
          className="flex items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white px-6 py-4 text-sm font-medium text-gray-900 transition-colors hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800"
        >
          <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          {downloading === "json" ? "Downloading..." : "Export JSON"}
        </button>
      </div>
    </div>
  );
}
