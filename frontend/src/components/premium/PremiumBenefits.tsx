"use client";

import { useAuth } from "@/components/auth/AuthProvider";

const FEATURES = [
  { name: "Historical Quantum Power Score charts", description: "Track score trends over 90 days to 1 year with 5 sub-metric breakdowns" },
  { name: "Full patent history timeline", description: "Browse all USPTO and EPO patents with searchable details and abstracts" },
  { name: "Insider trading alerts", description: "View SEC Form 4 filings showing when insiders buy or sell shares" },
  { name: "Institutional ownership changes", description: "Track 13F filings revealing institutional investor positions" },
  { name: "R&D spend ratio analysis", description: "Compare R&D investment intensity derived from SEC EDGAR XBRL data" },
  { name: "Government contract tracking", description: "Monitor federal contracts from USASpending.gov with award amounts" },
  { name: "CSV & JSON data export", description: "Download current rankings with all score components for your own analysis" },
  { name: "Email alerts on score changes", description: "Get notified when companies have significant score or filing changes" },
  { name: "REST API access", description: "Create API keys for programmatic access to all premium endpoints" },
  { name: "Ad-free experience", description: "No advertisements across the entire Chartora platform" },
];

export function PremiumBenefits() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-slate-900">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Your Premium Benefits</h3>
          <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700 dark:bg-green-900/50 dark:text-green-300">
            Active
          </span>
        </div>

        <p className="mb-6 text-sm text-gray-600 dark:text-slate-400">
          Your Chartora Pro subscription includes all of the following features.
        </p>

        <ul className="space-y-3">
          {FEATURES.map((feature) => (
            <li key={feature.name} className="flex items-start gap-3">
              <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400">
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </span>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{feature.name}</p>
                <p className="text-xs text-gray-500 dark:text-slate-400">{feature.description}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-slate-900">
        <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-slate-300">Subscription Details</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500 dark:text-slate-400">Email</span>
            <span className="text-gray-900 dark:text-white">{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500 dark:text-slate-400">Plan</span>
            <span className="text-gray-900 dark:text-white">Chartora Pro — $9/month</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500 dark:text-slate-400">Status</span>
            <span className="font-medium text-green-600 dark:text-green-400">Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
