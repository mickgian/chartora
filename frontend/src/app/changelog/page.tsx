import type { Metadata } from "next";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL || "https://chartora.com";

export const metadata: Metadata = {
  title: "Changelog | Chartora",
  description:
    "See what's new in Chartora. Release notes, new features, improvements, and bug fixes.",
  alternates: { canonical: `${SITE_URL}/changelog` },
};

interface ChangeEntry {
  version: string;
  date: string;
  title: string;
  changes: {
    category: "Added" | "Changed" | "Fixed";
    items: string[];
  }[];
}

const CHANGELOG_ENTRIES: ChangeEntry[] = [
  {
    version: "0.3.0",
    date: "2026-03-14",
    title: "Growth & Polish",
    changes: [
      {
        category: "Added",
        items: [
          "Methodology page with full scoring formula documentation",
          "About page with mission, data sources, and FAQ",
          "Changelog page with version history",
          "Launch page for Product Hunt preparation",
          "SEO improvements with JSON-LD structured data",
          "Social proof and data transparency sections",
        ],
      },
      {
        category: "Changed",
        items: [
          "Improved navigation with Methodology link",
          "Enhanced mobile responsiveness across all pages",
        ],
      },
      {
        category: "Fixed",
        items: [
          "Minor styling inconsistencies in dark mode",
        ],
      },
    ],
  },
  {
    version: "0.2.0",
    date: "2026-02-15",
    title: "Premium Features",
    changes: [
      {
        category: "Added",
        items: [
          "Premium dashboard with historical Quantum Power Score tracking",
          "Full patent history view for Pro users",
          "Insider trading alerts via SEC Form 4 monitoring",
          "Institutional ownership changes from 13F filings",
          "CSV and JSON data export",
          "Email alerts for score changes and milestones",
          "API access for Pro subscribers",
          "Ad-free experience for premium users",
          "Stripe payment integration",
          "User authentication with login and registration",
        ],
      },
      {
        category: "Changed",
        items: [
          "Redesigned company detail pages with more data density",
          "Improved chart rendering performance",
        ],
      },
    ],
  },
  {
    version: "0.1.0",
    date: "2026-01-10",
    title: "Initial Launch",
    changes: [
      {
        category: "Added",
        items: [
          "Main leaderboard with Quantum Power Score rankings",
          "Company detail pages with stock charts and patent timelines",
          "Metric deep-dive pages for stock performance, patents, funding, and sentiment",
          "Daily automated data pipeline with Yahoo Finance, USPTO, EPO, SEC EDGAR, and NewsAPI",
          "AI-powered news sentiment analysis via Claude API",
          "Responsive design with light and dark mode",
          "Tracking for 16 quantum computing companies and 2 ETFs",
          "Sortable and filterable leaderboard table",
        ],
      },
    ],
  },
];

const CATEGORY_STYLES: Record<ChangeEntry["changes"][number]["category"], { bg: string; text: string }> = {
  Added: {
    bg: "bg-emerald-100 dark:bg-emerald-900/40",
    text: "text-emerald-700 dark:text-emerald-400",
  },
  Changed: {
    bg: "bg-blue-100 dark:bg-blue-900/40",
    text: "text-blue-700 dark:text-blue-400",
  },
  Fixed: {
    bg: "bg-amber-100 dark:bg-amber-900/40",
    text: "text-amber-700 dark:text-amber-400",
  },
};

export default function ChangelogPage() {
  return (
    <>
      {/* Hero */}
      <section className="border-b border-gray-200 bg-gradient-to-b from-indigo-50 to-white py-16 dark:border-gray-800 dark:from-gray-900 dark:to-gray-950">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl dark:text-white">
            Changelog
          </h1>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
            New features, improvements, and fixes. Follow our progress as we
            build the best quantum computing tracker for investors.
          </p>
        </div>
      </section>

      {/* Timeline */}
      <section className="mx-auto max-w-3xl px-4 py-12">
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-[19px] top-2 hidden h-[calc(100%-1rem)] w-px bg-gray-200 sm:block dark:bg-gray-700" />

          <div className="space-y-12">
            {CHANGELOG_ENTRIES.map((entry, entryIndex) => (
              <div key={entry.version} className="relative sm:pl-14">
                {/* Timeline dot */}
                <div className="absolute left-2.5 top-1.5 hidden h-4 w-4 rounded-full border-2 border-indigo-500 bg-white sm:block dark:bg-gray-950">
                  {entryIndex === 0 && (
                    <div className="absolute inset-1 rounded-full bg-indigo-500" />
                  )}
                </div>

                {/* Header */}
                <div className="flex flex-wrap items-center gap-3">
                  <span className="rounded-full bg-indigo-100 px-3 py-1 text-sm font-semibold text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">
                    v{entry.version}
                  </span>
                  <time className="text-sm text-gray-500 dark:text-gray-400">
                    {new Date(entry.date).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </time>
                </div>

                <h2 className="mt-2 text-xl font-bold text-gray-900 dark:text-white">
                  {entry.title}
                </h2>

                {/* Changes */}
                <div className="mt-4 space-y-4">
                  {entry.changes.map((changeGroup) => {
                    const style = CATEGORY_STYLES[changeGroup.category];
                    return (
                      <div key={changeGroup.category}>
                        <span
                          className={`inline-block rounded px-2 py-0.5 text-xs font-semibold ${style.bg} ${style.text}`}
                        >
                          {changeGroup.category}
                        </span>
                        <ul className="mt-2 space-y-1.5">
                          {changeGroup.items.map((item) => (
                            <li
                              key={item}
                              className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400"
                            >
                              <svg
                                className="mt-0.5 h-4 w-4 shrink-0 text-gray-400 dark:text-gray-500"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M9 5l7 7-7 7"
                                />
                              </svg>
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
