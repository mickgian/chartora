import type { Metadata } from "next";
import Link from "next/link";
import { LaunchEmailForm } from "@/components/launch/LaunchEmailForm";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://chartora.com";

export const metadata: Metadata = {
  title: "Chartora Launch | The Quantum Computing Leaderboard for Investors",
  description:
    "Chartora ranks quantum computing companies by a composite Quantum Power Score. Free, auto-updating, and transparent. Get early access now.",
  alternates: { canonical: `${SITE_URL}/launch` },
};

const FEATURES = [
  {
    title: "Quantum Power Score",
    description:
      "A single 0-100 composite metric combining stock performance, patents, qubits, funding, and news sentiment.",
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    title: "Auto-Updating Daily",
    description:
      "Automated data pipelines refresh stock prices, patent filings, SEC data, and news sentiment every 24 hours.",
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
  },
  {
    title: "Deep Company Profiles",
    description:
      "Detailed pages for each company with stock charts, patent timelines, milestones, news feed, and competitor comparisons.",
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    title: "100% Free Core",
    description:
      "The full leaderboard, metric rankings, and company profiles are free forever. Premium adds historical data, alerts, and exports.",
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
];

const STATS = [
  { value: "16+", label: "Companies Tracked" },
  { value: "6", label: "Data Sources" },
  { value: "Daily", label: "Auto Updates" },
  { value: "5", label: "Scoring Dimensions" },
];

export default function LaunchPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-gray-200 bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 py-24 dark:border-gray-800">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxjaXJjbGUgY3g9IjMwIiBjeT0iMzAiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4xKSIvPjwvZz48L3N2Zz4=')] opacity-50" />
        <div className="relative mx-auto max-w-4xl px-4 text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5 text-sm font-medium text-white backdrop-blur">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Now Live
          </div>
          <h1 className="mt-6 text-4xl font-bold tracking-tight text-white sm:text-6xl">
            Track the Quantum
            <br />
            Computing Race
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-indigo-100">
            The free, auto-updating leaderboard that ranks quantum computing
            companies by a data-driven Quantum Power Score. Built for
            investors who want clarity in the most exciting sector of our time.
          </p>
          <div className="mt-10 flex flex-col items-center gap-4">
            <LaunchEmailForm />
            <p className="text-sm text-indigo-200">
              Join the waitlist for launch updates. No spam, unsubscribe
              anytime.
            </p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-5xl px-4 py-16">
        <h2 className="text-center text-2xl font-bold text-gray-900 sm:text-3xl dark:text-white">
          Everything you need to track quantum stocks
        </h2>
        <div className="mt-12 grid gap-8 sm:grid-cols-2">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-900"
            >
              <div className="text-indigo-600 dark:text-indigo-400">
                {feature.icon}
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900 dark:text-white">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Social Proof / Stats */}
      <section className="border-t border-gray-200 bg-gray-50 py-16 dark:border-gray-800 dark:bg-gray-900/50">
        <div className="mx-auto max-w-4xl px-4">
          <h2 className="text-center text-2xl font-bold text-gray-900 sm:text-3xl dark:text-white">
            Built on real data
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-gray-600 dark:text-gray-400">
            Chartora aggregates data from multiple free, publicly available
            sources to produce the most comprehensive view of the quantum
            computing landscape.
          </p>
          <div className="mt-12 grid grid-cols-2 gap-6 sm:grid-cols-4">
            {STATS.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                  {stat.value}
                </p>
                <p className="mt-1 text-sm font-medium text-gray-600 dark:text-gray-400">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="mx-auto max-w-4xl px-4 py-16 text-center">
        <h2 className="text-2xl font-bold text-gray-900 sm:text-3xl dark:text-white">
          Ready to explore the leaderboard?
        </h2>
        <p className="mt-4 text-gray-600 dark:text-gray-400">
          Start tracking quantum computing companies today. Free, no account
          required.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/"
            className="rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600"
          >
            View Leaderboard
          </Link>
          <Link
            href="/methodology"
            className="rounded-lg border border-gray-300 bg-white px-6 py-3 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Read Methodology
          </Link>
        </div>
      </section>
    </>
  );
}
