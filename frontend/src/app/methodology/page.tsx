import type { Metadata } from "next";
import Link from "next/link";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://chartora.com";

export const metadata: Metadata = {
  title: "Quantum Power Score Methodology | Chartora",
  description:
    "Learn how Chartora calculates the Quantum Power Score — a composite metric ranking quantum computing companies across stock momentum, patents, qubit progress, funding, and news sentiment.",
  openGraph: {
    title: "Quantum Power Score Methodology | Chartora",
    description:
      "Transparent methodology behind Chartora's Quantum Power Score for ranking quantum computing companies.",
    url: `${SITE_URL}/methodology`,
  },
};

interface ScoringComponent {
  title: string;
  weight: number;
  color: string;
  bgColor: string;
  icon: React.ReactNode;
  description: string;
  details: string[];
}

const SCORING_COMPONENTS: ScoringComponent[] = [
  {
    title: "Patent Velocity",
    weight: 25,
    color: "bg-purple-500",
    bgColor: "bg-purple-50 dark:bg-purple-950/30",
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    description:
      "Measures the rate of patent filings over the last 12 months, indicating active R&D investment and innovation velocity.",
    details: [
      "Counts patent applications filed in the trailing 12-month window",
      "Covers both US and European patent offices",
      "Normalized against the highest filer in our tracked universe",
      "Includes provisional and full patent applications",
    ],
  },
  {
    title: "Stock Momentum",
    weight: 20,
    color: "bg-green-500",
    bgColor: "bg-green-50 dark:bg-green-950/30",
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
    description:
      "Tracks share price performance over 30, 60, and 90-day windows to capture both short-term catalysts and medium-term trends.",
    details: [
      "Weighted average of 30-day (40%), 60-day (35%), and 90-day (25%) returns",
      "Benchmarked against the broader quantum computing sector",
      "Big-tech companies measured by quantum-segment proxy metrics",
      "ETFs use NAV performance data",
    ],
  },
  {
    title: "Qubit Progress",
    weight: 20,
    color: "bg-blue-500",
    bgColor: "bg-blue-50 dark:bg-blue-950/30",
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    description:
      "Evaluates the latest announced qubit count and quantum volume, reflecting a company's hardware capability and technological maturity.",
    details: [
      "Based on the most recently announced qubit count",
      "Considers quantum volume and error-correction milestones where available",
      "Normalized logarithmically to avoid outsized influence from leaders",
      "Updated when companies announce new processor milestones",
    ],
  },
  {
    title: "Funding Strength",
    weight: 20,
    color: "bg-amber-500",
    bgColor: "bg-amber-50 dark:bg-amber-950/30",
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    description:
      "Assesses total capital raised and financial strength using SEC regulatory filings — the same mandatory disclosures that institutional investors rely on.",
    details: [
      "Stockholders' equity or total assets from 10-K/10-Q filings",
      "Private placement amounts from Regulation D exempt offerings",
      "Government contract values included in total",
      "Score uses max(equity, private placements) + government contracts",
      "Normalized: $0 maps to 0, $1B+ maps to 100 (70% total weight, 30% recent round)",
      "All data pulled automatically — zero manual input or hardcoded values",
    ],
  },
  {
    title: "News Sentiment",
    weight: 15,
    color: "bg-rose-500",
    bgColor: "bg-rose-50 dark:bg-rose-950/30",
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
      </svg>
    ),
    description:
      "Analyzes recent news coverage using AI-powered sentiment analysis to capture market perception, partnerships, and breakthrough announcements.",
    details: [
      "Aggregates headlines from multiple news sources daily",
      "AI-scored sentiment on a -1 to +1 scale per article",
      "Weighted by source credibility and recency",
      "Rolling 30-day sentiment window with exponential decay",
    ],
  },
];

function WeightBar({ weight, color }: { weight: number; color: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-3 w-full max-w-48 overflow-hidden rounded-full bg-gray-200 dark:bg-slate-700">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${weight * 4}%` }}
        />
      </div>
      <span className="text-sm font-bold text-gray-900 dark:text-slate-100">
        {weight}%
      </span>
    </div>
  );
}

function ScoringSection({ component }: { component: ScoringComponent }) {
  return (
    <section className={`rounded-2xl border border-gray-200 p-6 sm:p-8 dark:border-gray-800 ${component.bgColor}`}>
      <div className="mb-4 flex items-start gap-4">
        <div className="flex-shrink-0 text-gray-700 dark:text-slate-300">
          {component.icon}
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 dark:text-slate-100">
            {component.title}
          </h3>
          <WeightBar weight={component.weight} color={component.color} />
        </div>
      </div>
      <p className="mb-4 text-gray-600 dark:text-slate-400">
        {component.description}
      </p>
      <div className="mb-4">
        <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-slate-400">
          How it works
        </h4>
        <ul className="space-y-1.5">
          {component.details.map((detail) => (
            <li key={detail} className="flex items-start gap-2 text-sm text-gray-600 dark:text-slate-400">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-gray-400 dark:bg-gray-500" />
              {detail}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export default function MethodologyPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: "Quantum Power Score Methodology",
    description:
      "Transparent methodology behind the Quantum Power Score used to rank quantum computing companies.",
    url: `${SITE_URL}/methodology`,
    publisher: {
      "@type": "Organization",
      name: "Chartora",
      url: SITE_URL,
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="mx-auto max-w-4xl px-4 py-12 sm:py-16">
        {/* Hero */}
        <div className="mb-12 text-center">
          <h1 className="mb-4 text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl dark:text-slate-100">
            Quantum Power Score
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-slate-400">
            A composite metric from 0 to 100 that ranks quantum computing
            companies across five fundamental dimensions. Designed to give
            investors a single, comparable benchmark for evaluating the quantum
            computing landscape.
          </p>
        </div>

        {/* Formula overview */}
        <div className="mb-12 rounded-2xl border border-indigo-200 bg-indigo-50 p-6 sm:p-8 dark:border-indigo-900 dark:bg-indigo-950/30">
          <h2 className="mb-4 text-lg font-bold text-indigo-900 dark:text-indigo-300">
            The Formula
          </h2>
          <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-sm leading-relaxed text-indigo-800 dark:text-indigo-300">
{`Quantum Power Score (0-100) =
  Stock Momentum  (20%)  → 30/60/90-day price performance
  Patent Velocity  (25%)  → Patents filed in last 12 months
  Qubit Progress   (20%)  → Latest announced qubit count
  Funding Strength (20%)  → Total raised + recent rounds + gov contracts
  News Sentiment   (15%)  → AI-scored recent coverage`}
          </pre>
          <p className="mt-3 text-xs text-indigo-700/80 dark:text-indigo-400/70">
            Every data point is sourced from publicly accessible government
            and financial data. No manual overrides.
          </p>
        </div>

        {/* Scoring components */}
        <div className="mb-16">
          <h2 className="mb-8 text-2xl font-bold text-gray-900 dark:text-slate-100">
            Scoring Components
          </h2>
          <div className="space-y-6">
            {SCORING_COMPONENTS.map((component) => (
              <ScoringSection key={component.title} component={component} />
            ))}
          </div>
        </div>

        {/* Data freshness */}
        <div className="mb-12 rounded-2xl border border-gray-200 bg-gray-50 p-6 sm:p-8 dark:border-gray-800 dark:bg-slate-900/50">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 text-gray-700 dark:text-slate-300">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <div>
              <h2 className="mb-2 text-xl font-bold text-gray-900 dark:text-slate-100">
                Data Freshness
              </h2>
              <p className="mb-3 text-gray-600 dark:text-slate-400">
                All scores are refreshed daily via an automated data pipeline.
                Our system fetches the latest data from all sources every 24
                hours, recalculates scores, and updates the leaderboard
                automatically.
              </p>
              <ul className="space-y-1.5">
                <li className="flex items-center gap-2 text-sm text-gray-600 dark:text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-green-500" />
                  Stock data updated every market day
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-600 dark:text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-green-500" />
                  Patent data refreshed daily from US and European patent offices
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-600 dark:text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-green-500" />
                  News sentiment analyzed daily with AI
                </li>
                <li className="flex items-center gap-2 text-sm text-gray-600 dark:text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-green-500" />
                  Funding and regulatory filings checked on each update cycle
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Transparency */}
        <div className="mb-12 rounded-2xl border border-gray-200 bg-gray-50 p-6 sm:p-8 dark:border-gray-800 dark:bg-slate-900/50">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 text-gray-700 dark:text-slate-300">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <div>
              <h2 className="mb-2 text-xl font-bold text-gray-900 dark:text-slate-100">
                Transparency & Open Methodology
              </h2>
              <p className="mb-3 text-gray-600 dark:text-slate-400">
                We believe in full transparency. Our scoring methodology is
                published here for anyone to review and critique. Every data
                source is publicly accessible, and our weights are chosen based
                on what matters most to quantum computing investors.
              </p>
              <p className="text-gray-600 dark:text-slate-400">
                No black boxes. No hidden factors. If a company&apos;s score
                changes, you can trace exactly why through the individual
                component scores visible on each{" "}
                <Link href="/company/ionq" className="text-indigo-600 underline hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300">
                  company detail page
                </Link>
                .
              </p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <p className="mb-4 text-gray-600 dark:text-slate-400">
            See the Quantum Power Score in action on the leaderboard.
          </p>
          <Link
            href="/"
            className="inline-block rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600"
          >
            View Leaderboard
          </Link>
        </div>
      </div>
    </>
  );
}
