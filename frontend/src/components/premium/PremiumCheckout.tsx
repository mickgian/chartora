"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const FEATURES = [
  "Historical Quantum Power Score charts",
  "Full patent history timeline",
  "Insider trading alerts",
  "Institutional ownership changes",
  "R&D spend ratio analysis",
  "Government contract tracking",
  "CSV & JSON data export",
  "Email alerts on score changes",
  "REST API access",
  "Ad-free experience",
];

export function PremiumCheckout() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCheckout(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/api/v1/payments/create-checkout-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Failed to create checkout session");
      }

      const data = await res.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Chartora Pro</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Premium quantum computing intelligence for serious investors.
        </p>
      </div>

      <div className="mt-8 rounded-xl border-2 border-indigo-200 bg-white p-8 shadow-sm dark:border-indigo-800 dark:bg-gray-900">
        <div className="mb-6 text-center">
          <span className="text-4xl font-bold text-gray-900 dark:text-white">$9</span>
          <span className="text-gray-500 dark:text-gray-400">/month</span>
        </div>

        <ul className="mb-8 space-y-3">
          {FEATURES.map((feature) => (
            <li key={feature} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
              <span className="mt-0.5 text-indigo-500">&#10003;</span>
              {feature}
            </li>
          ))}
        </ul>

        <form onSubmit={handleCheckout} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Email address
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:ring-indigo-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 dark:text-red-400" data-testid="checkout-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-indigo-600 px-4 py-3 font-medium text-white transition-colors hover:bg-indigo-700 disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-600"
            data-testid="checkout-button"
          >
            {loading ? "Redirecting to checkout..." : "Subscribe — $9/month"}
          </button>
        </form>
      </div>

      <p className="mt-4 text-center text-xs text-gray-400 dark:text-gray-500">
        Payments processed securely by Stripe. Cancel anytime.
      </p>
    </div>
  );
}
