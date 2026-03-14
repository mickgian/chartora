"use client";

import { useAuth } from "@/components/auth/AuthProvider";
import { PremiumDashboard } from "@/components/premium/PremiumDashboard";
import Link from "next/link";

export default function ProDashboardPage() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-md text-center py-20">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Sign in required</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Please sign in to access your dashboard.
        </p>
        <Link
          href="/login"
          className="mt-4 inline-block rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700"
        >
          Sign in
        </Link>
      </div>
    );
  }

  if (!user.is_premium) {
    return (
      <div className="mx-auto max-w-md text-center py-20">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Premium required</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Upgrade to Chartora Pro to access the premium dashboard.
        </p>
        <Link
          href="/pro"
          className="mt-4 inline-block rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700"
        >
          Subscribe — $9/month
        </Link>
      </div>
    );
  }

  return <PremiumDashboard />;
}
