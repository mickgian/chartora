"use client";

import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface AlertPref {
  id: number | null;
  alert_type: string;
  enabled: boolean;
  threshold: number | null;
}

const ALERT_TYPES = [
  {
    type: "score_change",
    label: "Score change alerts",
    description: "Get notified when a company's Quantum Power Score changes significantly.",
    hasThreshold: true,
    defaultThreshold: 10,
  },
  {
    type: "insider_trading",
    label: "Insider trading alerts",
    description: "Get notified when new insider trading (Form 4) filings are detected.",
    hasThreshold: false,
    defaultThreshold: null,
  },
  {
    type: "institutional_ownership",
    label: "Institutional ownership alerts",
    description: "Get notified when new 13F institutional ownership filings are detected.",
    hasThreshold: false,
    defaultThreshold: null,
  },
  {
    type: "government_contract",
    label: "Government contract alerts",
    description: "Get notified when new government contracts are awarded to tracked companies.",
    hasThreshold: false,
    defaultThreshold: null,
  },
];

function getToken(): string {
  return localStorage.getItem("chartora_access_token") ?? "";
}

export function AlertPreferences() {
  const [prefs, setPrefs] = useState<AlertPref[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchPrefs = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/pro/alerts`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPrefs(data.alerts ?? []);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPrefs();
  }, [fetchPrefs]);

  function getAlertPref(alertType: string): AlertPref | undefined {
    return prefs.find((p) => p.alert_type === alertType);
  }

  function toggleAlert(alertType: string) {
    setPrefs((prev) => {
      const existing = prev.find((p) => p.alert_type === alertType);
      if (existing) {
        return prev.map((p) =>
          p.alert_type === alertType ? { ...p, enabled: !p.enabled } : p,
        );
      }
      return [...prev, { id: null, alert_type: alertType, enabled: true, threshold: null }];
    });
  }

  function setThreshold(alertType: string, value: number) {
    setPrefs((prev) =>
      prev.map((p) =>
        p.alert_type === alertType ? { ...p, threshold: value } : p,
      ),
    );
  }

  async function handleSave() {
    setSaving(true);
    setMessage(null);

    const alertsToSave = ALERT_TYPES.map((at) => {
      const pref = getAlertPref(at.type);
      return {
        alert_type: at.type,
        enabled: pref?.enabled ?? false,
        threshold: pref?.threshold ?? at.defaultThreshold,
      };
    });

    try {
      const res = await fetch(`${API_URL}/api/v1/pro/alerts`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ alerts: alertsToSave }),
      });

      if (res.ok) {
        const data = await res.json();
        setPrefs(data.alerts ?? []);
        setMessage("Preferences saved.");
      } else {
        setMessage("Failed to save preferences.");
      }
    } catch {
      setMessage("Failed to save preferences.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="py-8 text-center text-sm text-gray-500">Loading preferences...</div>;
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-600 dark:text-slate-400">
        Configure email alerts for quantum computing market events.
      </p>

      {ALERT_TYPES.map((at) => {
        const pref = getAlertPref(at.type);
        const enabled = pref?.enabled ?? false;

        return (
          <div
            key={at.type}
            className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-slate-900"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white">{at.label}</h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-slate-400">{at.description}</p>
              </div>
              <button
                onClick={() => toggleAlert(at.type)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  enabled ? "bg-indigo-600" : "bg-gray-300 dark:bg-slate-700"
                }`}
                aria-label={`Toggle ${at.label}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    enabled ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>

            {at.hasThreshold && enabled && (
              <div className="mt-3 flex items-center gap-2">
                <label className="text-sm text-gray-600 dark:text-slate-400">
                  Threshold (points):
                </label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={pref?.threshold ?? at.defaultThreshold ?? 10}
                  onChange={(e) => setThreshold(at.type, Number(e.target.value))}
                  className="w-20 rounded-lg border border-gray-300 px-2 py-1 text-sm dark:border-gray-700 dark:bg-slate-800/80 dark:text-white"
                />
              </div>
            )}
          </div>
        );
      })}

      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save preferences"}
        </button>
        {message && (
          <span className="text-sm text-gray-600 dark:text-slate-400">{message}</span>
        )}
      </div>
    </div>
  );
}
