"use client";

import { useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { CompanySelector } from "./CompanySelector";
import { HistoricalScoreChart } from "./HistoricalScoreChart";
import { RdSpendingCard } from "./RdSpendingCard";
import { InsiderTradingTable } from "./InsiderTradingTable";
import { InstitutionalOwnershipTable } from "./InstitutionalOwnershipTable";
import { FullPatentHistory } from "./FullPatentHistory";
import { GovernmentContracts } from "./GovernmentContracts";
import { AlertPreferences } from "./AlertPreferences";
import { ApiKeyManager } from "./ApiKeyManager";
import { ExportButtons } from "./ExportButtons";
import { PremiumBenefits } from "./PremiumBenefits";

const TABS = [
  { id: "score-analytics", label: "Score Analytics" },
  { id: "sec-filings", label: "SEC Filings" },
  { id: "patents-contracts", label: "Patents & Contracts" },
  { id: "alerts", label: "Alerts" },
  { id: "exports-api", label: "Exports & API" },
  { id: "benefits", label: "Your Benefits" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const COMPANY_TABS = new Set<TabId>(["score-analytics", "sec-filings", "patents-contracts"]);

export function PremiumDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>("score-analytics");
  const [selectedSlug, setSelectedSlug] = useState("");
  const [period, setPeriod] = useState(365);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Premium Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Welcome back, {user?.email}
          </p>
        </div>
        <span className="rounded-full bg-indigo-100 px-3 py-1 text-sm font-semibold text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300">
          PRO
        </span>
      </div>

      <div className="mb-6 flex gap-1 overflow-x-auto rounded-lg bg-gray-100 p-1 dark:bg-slate-800/80">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? "bg-white text-gray-900 shadow-sm dark:bg-slate-700 dark:text-white"
                : "text-gray-600 hover:text-gray-900 dark:text-slate-400 dark:hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Persistent company selector for data tabs */}
      {COMPANY_TABS.has(activeTab) && (
        <div className="mb-6">
          <CompanySelector
            selectedSlug={selectedSlug}
            onSlugChange={setSelectedSlug}
            showPeriod={activeTab === "score-analytics"}
            period={period}
            onPeriodChange={setPeriod}
          />
        </div>
      )}

      {activeTab === "score-analytics" && selectedSlug && (
        <div className="space-y-6">
          <HistoricalScoreChart slug={selectedSlug} period={period} />
          <RdSpendingCard slug={selectedSlug} />
        </div>
      )}

      {activeTab === "sec-filings" && selectedSlug && (
        <div className="space-y-6">
          <InsiderTradingTable slug={selectedSlug} />
          <InstitutionalOwnershipTable slug={selectedSlug} />
        </div>
      )}

      {activeTab === "patents-contracts" && selectedSlug && (
        <div className="space-y-6">
          <FullPatentHistory slug={selectedSlug} />
          <GovernmentContracts slug={selectedSlug} />
        </div>
      )}

      {activeTab === "alerts" && <AlertPreferences />}

      {activeTab === "exports-api" && (
        <div className="space-y-8">
          <ExportButtons />
          <div className="border-t border-gray-200 pt-8 dark:border-gray-700">
            <ApiKeyManager />
          </div>
        </div>
      )}

      {activeTab === "benefits" && <PremiumBenefits />}
    </div>
  );
}
