"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface CompanyOption {
  slug: string;
  name: string;
}

const PERIOD_OPTIONS = [
  { value: 90, label: "90 days" },
  { value: 180, label: "6 months" },
  { value: 365, label: "1 year" },
];

interface CompanySelectorProps {
  selectedSlug: string;
  onSlugChange: (slug: string) => void;
  showPeriod?: boolean;
  period?: number;
  onPeriodChange?: (days: number) => void;
}

export function CompanySelector({
  selectedSlug,
  onSlugChange,
  showPeriod = false,
  period = 365,
  onPeriodChange,
}: CompanySelectorProps) {
  const [companies, setCompanies] = useState<CompanyOption[]>([]);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/leaderboard`)
      .then((res) => res.json())
      .then((data) => {
        const opts =
          data.entries?.map((e: { company: CompanyOption }) => ({
            slug: e.company.slug,
            name: e.company.name,
          })) ?? [];
        setCompanies(opts);
        if (opts.length > 0 && !selectedSlug) {
          onSlugChange(opts[0].slug);
        }
      })
      .catch(() => setCompanies([]));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex flex-wrap items-center gap-4">
      <select
        value={selectedSlug}
        onChange={(e) => onSlugChange(e.target.value)}
        className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-slate-800/80 dark:text-white"
      >
        {companies.map((c) => (
          <option key={c.slug} value={c.slug}>
            {c.name}
          </option>
        ))}
      </select>

      {showPeriod && onPeriodChange && (
        <div className="flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-slate-800/80">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onPeriodChange(opt.value)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                period === opt.value
                  ? "bg-white text-gray-900 shadow-sm dark:bg-slate-700 dark:text-white"
                  : "text-gray-500 hover:text-gray-700 dark:text-slate-400"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
