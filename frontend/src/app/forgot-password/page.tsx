"use client";

import Link from "next/link";
import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/password-reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Request failed");
      }

      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  if (sent) {
    return (
      <div className="mx-auto max-w-md text-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Check your email</h1>
        <p className="mt-2 text-gray-600 dark:text-slate-400">
          If an account exists for <strong>{email}</strong>, we&apos;ve sent a password reset link.
        </p>
        <Link
          href="/login"
          className="mt-6 inline-block text-indigo-600 hover:underline dark:text-indigo-400"
        >
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reset password</h1>
      <p className="mt-1 text-sm text-gray-600 dark:text-slate-400">
        Enter your email and we&apos;ll send you a reset link.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-slate-300">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-indigo-500 focus:ring-indigo-500 dark:border-gray-700 dark:bg-slate-800/80 dark:text-white"
          />
        </div>

        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 font-medium text-white transition-colors hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Sending..." : "Send reset link"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-gray-600 dark:text-slate-400">
        Remember your password?{" "}
        <Link href="/login" className="text-indigo-600 hover:underline dark:text-indigo-400">
          Sign in
        </Link>
      </p>
    </div>
  );
}
