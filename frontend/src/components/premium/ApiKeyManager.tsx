"use client";

import { useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ApiKeyInfo {
  id: number;
  name: string;
  prefix: string;
  created_at: string | null;
  last_used_at: string | null;
  is_active: boolean;
}

function getToken(): string {
  return localStorage.getItem("chartora_access_token") ?? "";
}

export function ApiKeyManager() {
  const [keys, setKeys] = useState<ApiKeyInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const fetchKeys = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/pro/api-keys`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        const data = await res.json();
        setKeys(data.api_keys ?? []);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  async function handleCreate() {
    if (!newKeyName.trim()) return;
    setCreating(true);
    setCreatedKey(null);

    try {
      const res = await fetch(`${API_URL}/api/v1/pro/api-keys`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ name: newKeyName }),
      });

      if (res.ok) {
        const data = await res.json();
        setCreatedKey(data.api_key);
        setNewKeyName("");
        fetchKeys();
      }
    } catch {
      // ignore
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke(keyId: number) {
    try {
      await fetch(`${API_URL}/api/v1/pro/api-keys/${keyId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      setKeys((prev) => prev.filter((k) => k.id !== keyId));
    } catch {
      // ignore
    }
  }

  if (loading) {
    return <div className="py-8 text-center text-sm text-gray-500">Loading API keys...</div>;
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Create API keys for programmatic access to Chartora premium endpoints.
      </p>

      {/* Create new key */}
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Key name (e.g. My App)"
          value={newKeyName}
          onChange={(e) => setNewKeyName(e.target.value)}
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800 dark:text-white"
        />
        <button
          onClick={handleCreate}
          disabled={creating || !newKeyName.trim()}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {creating ? "Creating..." : "Create key"}
        </button>
      </div>

      {/* Newly created key */}
      {createdKey && (
        <div className="rounded-xl border-2 border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
          <p className="text-sm font-medium text-green-800 dark:text-green-300">
            Save this key — it won&apos;t be shown again:
          </p>
          <code className="mt-2 block break-all rounded bg-green-100 p-2 text-sm dark:bg-green-900/40 dark:text-green-200">
            {createdKey}
          </code>
        </div>
      )}

      {/* Existing keys */}
      {keys.length > 0 ? (
        <div className="space-y-2">
          {keys.map((key) => (
            <div
              key={key.id}
              className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900"
            >
              <div>
                <p className="font-medium text-gray-900 dark:text-white">{key.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {key.prefix}... &middot;{" "}
                  {key.created_at
                    ? `Created ${new Date(key.created_at).toLocaleDateString()}`
                    : ""}
                  {key.last_used_at
                    ? ` &middot; Last used ${new Date(key.last_used_at).toLocaleDateString()}`
                    : ""}
                </p>
              </div>
              <button
                onClick={() => handleRevoke(key.id)}
                className="text-sm text-red-600 hover:underline dark:text-red-400"
              >
                Revoke
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-500">No API keys yet.</p>
      )}
    </div>
  );
}
