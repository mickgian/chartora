"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login(email, password);
      router.push("/pro/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Sign in</h1>
      <p className="mt-1 text-sm text-gray-600 dark:text-slate-400">
        Access your Chartora Pro account.
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

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-slate-300">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-indigo-500 focus:ring-indigo-500 dark:border-gray-700 dark:bg-slate-800/80 dark:text-white"
          />
        </div>

        {error && (
          <p className="text-sm text-red-600 dark:text-red-400" data-testid="login-error">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 font-medium text-white transition-colors hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <div className="mt-4 space-y-2 text-center text-sm">
        <p className="text-gray-600 dark:text-slate-400">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-indigo-600 hover:underline dark:text-indigo-400">
            Sign up
          </Link>
        </p>
        <p>
          <Link
            href="/forgot-password"
            className="text-gray-500 hover:underline dark:text-slate-400"
          >
            Forgot your password?
          </Link>
        </p>
      </div>
    </div>
  );
}
