"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";

const NAV_LINKS = [
  { href: "/", label: "Leaderboard" },
  { href: "/rankings/stock-performance", label: "Stock" },
  { href: "/rankings/patents", label: "Patents" },
  { href: "/rankings/funding", label: "Funding" },
  { href: "/rankings/sentiment", label: "Sentiment" },
  { href: "/methodology", label: "Methodology" },
];

export function Header() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur dark:border-slate-700 dark:bg-slate-900/95">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 text-xl font-bold">
          <span className="text-indigo-600 dark:text-indigo-300">&#9883;</span>
          <span>Chartora</span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-gray-600 transition-colors hover:text-gray-900 dark:text-slate-300 dark:hover:text-slate-50"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              {user.is_premium && (
                <span className="hidden rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 md:inline-block dark:bg-indigo-900/60 dark:text-indigo-300" data-testid="premium-badge">
                  PRO
                </span>
              )}
              <Link
                href="/pro/dashboard"
                className="hidden text-sm font-medium text-gray-600 transition-colors hover:text-gray-900 md:inline-block dark:text-slate-300 dark:hover:text-slate-50"
              >
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="hidden text-sm font-medium text-gray-500 transition-colors hover:text-gray-700 md:inline-block dark:text-slate-300 dark:hover:text-slate-100"
                data-testid="logout-button"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="hidden text-sm font-medium text-gray-600 transition-colors hover:text-gray-900 md:inline-block dark:text-slate-300 dark:hover:text-slate-50"
              >
                Sign in
              </Link>
              <Link
                href="/pro"
                className="hidden rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-indigo-700 md:inline-block dark:bg-indigo-500 dark:hover:bg-indigo-600"
              >
                Go Pro
              </Link>
            </>
          )}
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 md:hidden dark:text-slate-300 dark:hover:bg-slate-700"
            aria-label="Toggle menu"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {menuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>
      </div>

      {menuOpen && (
        <nav className="border-t border-gray-200 bg-white px-4 py-3 md:hidden dark:border-slate-700 dark:bg-slate-900">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className="block rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              {link.label}
            </Link>
          ))}
          {user ? (
            <>
              <Link
                href="/pro/dashboard"
                onClick={() => setMenuOpen(false)}
                className="block rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                Dashboard {user.is_premium && "(PRO)"}
              </Link>
              <button
                onClick={() => {
                  logout();
                  setMenuOpen(false);
                }}
                className="block w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-gray-500 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                onClick={() => setMenuOpen(false)}
                className="block rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                Sign in
              </Link>
              <Link
                href="/pro"
                onClick={() => setMenuOpen(false)}
                className="block rounded-lg px-3 py-2 text-sm font-semibold text-indigo-600 hover:bg-indigo-50 dark:text-indigo-300 dark:hover:bg-indigo-900/40"
              >
                Go Pro
              </Link>
            </>
          )}
        </nav>
      )}
    </header>
  );
}
