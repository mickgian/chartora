import type { Metadata } from "next";
import Link from "next/link";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://chartora.com";

export const metadata: Metadata = {
  title: "About Chartora | Quantum Computing Leaderboard for Investors",
  description:
    "Chartora is a free, auto-updating leaderboard that ranks quantum computing companies by a composite Quantum Power Score. Built for investors tracking the quantum revolution.",
  openGraph: {
    title: "About Chartora",
    description:
      "Free, data-driven quantum computing leaderboard for investors.",
    url: `${SITE_URL}/about`,
  },
};

const VALUE_PROPS = [
  {
    title: "Free & Accessible",
    description:
      "Core leaderboard and company rankings are completely free. No paywall for essential data.",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    title: "Data-Driven Rankings",
    description:
      "Every score is backed by real data from public APIs — stock prices, patent filings, SEC filings, and news sentiment.",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    title: "Auto-Updating",
    description:
      "Our automated pipeline refreshes data daily. No manual curation — scores stay current without intervention.",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
  },
  {
    title: "Transparent Methodology",
    description:
      "Our scoring formula is fully published. Every weight, every data source, every calculation — open for scrutiny.",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </svg>
    ),
  },
];

const DATA_SOURCES = [
  { name: "Yahoo Finance", usage: "Stock prices, market cap, historical performance" },
  { name: "USPTO Patent API", usage: "US patent filings and grants" },
  { name: "EPO OPS API", usage: "European patent filings" },
  { name: "SEC EDGAR XBRL", usage: "Stockholders' equity and total assets from 10-K/10-Q filings" },
  { name: "SEC EDGAR Form D", usage: "Private placement fundraising amounts (Reg D exempt offerings)" },
  { name: "SEC EDGAR Filings", usage: "Insider trades (Form 4), institutional ownership (13F), material events (8-K)" },
  { name: "NewsAPI.org", usage: "News headlines aggregation" },
  { name: "Claude API", usage: "AI-powered news sentiment analysis" },
  { name: "Wikipedia API", usage: "Company descriptions and background" },
  { name: "USASpending.gov", usage: "Federal government contract awards" },
];

const FAQS = [
  {
    question: "How often is the data updated?",
    answer:
      "All data is refreshed daily via our automated pipeline. Stock data updates every market day, patent and filing data is checked daily, and news sentiment is analyzed with each update cycle.",
  },
  {
    question: "Which companies does Chartora track?",
    answer:
      "We track pure-play quantum companies (IonQ, D-Wave, Rigetti, Quantum Computing Inc, Arqit, Zapata), big tech with quantum divisions (IBM, Google, Microsoft, Amazon, Intel, Honeywell/Quantinuum), and quantum-focused ETFs (QTUM, ARKX).",
  },
  {
    question: "Is the Quantum Power Score financial advice?",
    answer:
      "No. The Quantum Power Score is an informational tool for research purposes only. It is not financial advice, and you should always do your own due diligence before making investment decisions.",
  },
  {
    question: "What is included in the Pro plan?",
    answer:
      "Pro subscribers get access to historical Power Score trends, full patent history, insider trading alerts, institutional ownership changes, CSV/JSON data export, email alerts, API access, and an ad-free experience.",
  },
  {
    question: "How is the Quantum Power Score calculated?",
    answer:
      "The score combines five weighted components: Stock Momentum (20%), Patent Velocity (25%), Qubit Progress (20%), Funding Strength (20%), and News Sentiment (15%). Full details are available on our Methodology page.",
  },
  {
    question: "Can I suggest a company to track?",
    answer:
      "Absolutely! We are always looking to expand our coverage. Reach out to us and we will evaluate adding new companies to the leaderboard.",
  },
];

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:py-16">
      {/* Hero / Mission */}
      <div className="mb-16 text-center">
        <h1 className="mb-4 text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl dark:text-slate-100">
          About Chartora
        </h1>
        <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-slate-400">
          Chartora is a free, auto-updating leaderboard that ranks quantum
          computing companies using publicly available data. We built it so
          investors can track the quantum revolution in one place — without
          paywalls, black-box scores, or stale data.
        </p>
      </div>

      {/* Why Chartora */}
      <section className="mb-16">
        <h2 className="mb-8 text-center text-2xl font-bold text-gray-900 dark:text-slate-100">
          Why Chartora?
        </h2>
        <div className="grid gap-6 sm:grid-cols-2">
          {VALUE_PROPS.map((prop) => (
            <div
              key={prop.title}
              className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-slate-900/50"
            >
              <div className="mb-3 text-indigo-600 dark:text-indigo-400">
                {prop.icon}
              </div>
              <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-slate-100">
                {prop.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-slate-400">
                {prop.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Data Sources */}
      <section className="mb-16">
        <h2 className="mb-6 text-2xl font-bold text-gray-900 dark:text-slate-100">
          Data Sources
        </h2>
        <p className="mb-6 text-gray-600 dark:text-slate-400">
          Chartora pulls data exclusively from free, publicly available APIs.
          Every data point feeding into the Quantum Power Score can be
          independently verified.
        </p>
        <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 dark:bg-slate-900">
              <tr>
                <th className="px-4 py-3 font-semibold text-gray-700 dark:text-slate-300">
                  Source
                </th>
                <th className="px-4 py-3 font-semibold text-gray-700 dark:text-slate-300">
                  Data Provided
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {DATA_SOURCES.map((source) => (
                <tr key={source.name} className="bg-white dark:bg-gray-950">
                  <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900 dark:text-slate-100">
                    {source.name}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-slate-400">
                    {source.usage}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Team / Credibility */}
      <section className="mb-16 rounded-2xl border border-gray-200 bg-gray-50 p-6 sm:p-8 dark:border-gray-800 dark:bg-slate-900/50">
        <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-slate-100">
          Built by Enthusiasts
        </h2>
        <p className="mb-3 text-gray-600 dark:text-slate-400">
          Chartora is built by a team of quantum computing and financial data
          enthusiasts who saw a gap in the market: there was no single,
          transparent, auto-updating resource for investors to compare quantum
          computing companies side by side.
        </p>
        <p className="text-gray-600 dark:text-slate-400">
          We combine expertise in data engineering, financial analysis, and
          software development to deliver a product that stays current, stays
          accurate, and stays free at its core.
        </p>
      </section>

      {/* FAQ */}
      <section className="mb-16">
        <h2 className="mb-8 text-2xl font-bold text-gray-900 dark:text-slate-100">
          Frequently Asked Questions
        </h2>
        <div className="space-y-6">
          {FAQS.map((faq) => (
            <div key={faq.question}>
              <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-slate-100">
                {faq.question}
              </h3>
              <p className="text-gray-600 dark:text-slate-400">{faq.answer}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-8 text-center dark:border-indigo-900 dark:bg-indigo-950/30">
        <h2 className="mb-3 text-2xl font-bold text-gray-900 dark:text-slate-100">
          Ready to go deeper?
        </h2>
        <p className="mb-6 text-gray-600 dark:text-slate-400">
          Unlock historical trends, insider trading alerts, data exports, and
          more with Chartora Pro.
        </p>
        <Link
          href="/pro"
          className="inline-block rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600"
        >
          Go Pro
        </Link>
      </div>
    </div>
  );
}
