import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <Link href="/" className="font-semibold text-gray-700 dark:text-gray-300">
              Chartora
            </Link>{" "}
            — Quantum Computing Company Rankings
          </div>
          <nav className="flex gap-6 text-sm text-gray-500 dark:text-gray-400">
            <Link href="/" className="hover:text-gray-700 dark:hover:text-gray-300">
              Leaderboard
            </Link>
            <Link
              href="/rankings/stock-performance"
              className="hover:text-gray-700 dark:hover:text-gray-300"
            >
              Rankings
            </Link>
          </nav>
        </div>
        <div className="mt-6 text-center text-xs text-gray-400 dark:text-gray-500">
          Data sourced from Yahoo Finance, USPTO, SEC EDGAR, and NewsAPI. Not financial advice.
        </div>
      </div>
    </footer>
  );
}
