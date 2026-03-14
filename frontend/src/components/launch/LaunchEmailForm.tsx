"use client";

import { useState } from "react";

const STORAGE_KEY = "chartora_launch_emails";

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function LaunchEmailForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");

    const trimmed = email.trim();
    if (!trimmed) {
      setError("Please enter your email address.");
      return;
    }
    if (!isValidEmail(trimmed)) {
      setError("Please enter a valid email address.");
      return;
    }

    try {
      const existing = localStorage.getItem(STORAGE_KEY);
      const emails: string[] = existing ? (JSON.parse(existing) as string[]) : [];
      if (!emails.includes(trimmed)) {
        emails.push(trimmed);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(emails));
      }
    } catch {
      // localStorage might be unavailable; proceed anyway
    }

    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-6 py-4 dark:border-emerald-800 dark:bg-emerald-900/30">
        <svg
          className="h-6 w-6 shrink-0 text-emerald-600 dark:text-emerald-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="font-semibold text-emerald-700 dark:text-emerald-300">
          You&rsquo;re on the list! We&rsquo;ll notify you at launch.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-md">
      <div className="flex gap-2">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          aria-label="Email address"
          className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500 dark:focus:border-indigo-400 dark:focus:ring-indigo-400/20"
        />
        <button
          type="submit"
          className="shrink-0 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600"
        >
          Get Early Access
        </button>
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </form>
  );
}
