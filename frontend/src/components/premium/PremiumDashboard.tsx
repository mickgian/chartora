"use client";

import { useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { HistoricalScoreChart } from "./HistoricalScoreChart";
import { AlertPreferences } from "./AlertPreferences";
import { ApiKeyManager } from "./ApiKeyManager";
import { ExportButtons } from "./ExportButtons";

const TABS = [
  { id: "historical", label: "Historical Data" },
  { id: "alerts", label: "Alerts" },
  { id: "exports", label: "Exports" },
  { id: "api-keys", label: "API Keys" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export function PremiumDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>("historical");

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Premium Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Welcome back, {user?.email}
          </p>
        </div>
        <span className="rounded-full bg-indigo-100 px-3 py-1 text-sm font-semibold text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300">
          PRO
        </span>
      </div>

      <div className="mb-6 flex gap-1 overflow-x-auto rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? "bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white"
                : "text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "historical" && <HistoricalScoreChart />}
      {activeTab === "alerts" && <AlertPreferences />}
      {activeTab === "exports" && <ExportButtons />}
      {activeTab === "api-keys" && <ApiKeyManager />}
    </div>
  );
}
