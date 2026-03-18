import Link from "next/link";
import { AdSlot } from "@/components/ads/AdSlot";

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50 dark:border-slate-700 dark:bg-slate-900">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <AdSlot adSlot="footer-banner" placement="footer" className="mb-6" />
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="text-sm text-gray-500 dark:text-slate-400">
            <Link href="/" className="font-semibold text-gray-700 dark:text-slate-200">
              Chartora
            </Link>{" "}
            — Quantum Computing Company Rankings
          </div>
          <nav className="flex gap-6 text-sm text-gray-500 dark:text-slate-400">
            <Link href="/" className="hover:text-gray-700 dark:hover:text-slate-300">
              Leaderboard
            </Link>
            <Link
              href="/rankings/stock-performance"
              className="hover:text-gray-700 dark:hover:text-slate-300"
            >
              Rankings
            </Link>
          </nav>
        </div>
        <div className="mt-6 text-center text-xs text-gray-400 dark:text-slate-500">
          Data sourced from public financial and regulatory filings. Not financial advice.
        </div>
      </div>
    </footer>
  );
}
