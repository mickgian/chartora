"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { useTheme } from "./ThemeProvider";

const NAV_LINKS = [
  { href: "/", label: "Leaderboard" },
  { href: "/rankings/stock-performance", label: "Stock" },
  { href: "/rankings/patents", label: "Patents" },
  { href: "/rankings/funding", label: "Funding" },
  { href: "/rankings/sentiment", label: "Sentiment" },
  { href: "/methodology", label: "Methodology" },
];

export function Header() {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur dark:border-gray-800 dark:bg-gray-950/80">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 text-xl font-bold">
          <span className="text-indigo-600 dark:text-indigo-400">&#9883;</span>
          <span>Chartora</span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-gray-600 transition-colors hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              {user.is_premium && (
                <span className="hidden rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 md:inline-block dark:bg-indigo-900/50 dark:text-indigo-300" data-testid="premium-badge">
                  PRO
                </span>
              )}
              <Link
                href="/pro/dashboard"
                className="hidden text-sm font-medium text-gray-600 transition-colors hover:text-gray-900 md:inline-block dark:text-gray-400 dark:hover:text-gray-100"
              >
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="hidden text-sm font-medium text-gray-500 transition-colors hover:text-gray-700 md:inline-block dark:text-gray-400 dark:hover:text-gray-200"
                data-testid="logout-button"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="hidden text-sm font-medium text-gray-600 transition-colors hover:text-gray-900 md:inline-block dark:text-gray-400 dark:hover:text-gray-100"
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
            onClick={toggleTheme}
            className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          >
            {theme === "light" ? (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
            )}
          </button>

          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 md:hidden dark:text-gray-400 dark:hover:bg-gray-800"
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
        <nav className="border-t border-gray-200 bg-white px-4 py-3 md:hidden dark:border-gray-800 dark:bg-gray-950">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className="block rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            >
              {link.label}
            </Link>
          ))}
          {user ? (
            <>
              <Link
                href="/pro/dashboard"
                onClick={() => setMenuOpen(false)}
                className="block rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              >
                Dashboard {user.is_premium && "(PRO)"}
              </Link>
              <button
                onClick={() => {
                  logout();
                  setMenuOpen(false);
                }}
                className="block w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                onClick={() => setMenuOpen(false)}
                className="block rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              >
                Sign in
              </Link>
              <Link
                href="/pro"
                onClick={() => setMenuOpen(false)}
                className="block rounded-lg px-3 py-2 text-sm font-semibold text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-950/30"
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
