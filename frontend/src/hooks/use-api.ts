/**
 * Custom hooks for data fetching with loading/error states.
 */

"use client";

import { useCallback, useEffect, useState } from "react";

export interface UseApiResult<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refetch: () => void;
}

/* eslint-disable no-console */
const hookLog = {
  info: (...args: unknown[]) => console.log("[useApi]", ...args),
  warn: (...args: unknown[]) => console.warn("[useApi]", ...args),
  error: (...args: unknown[]) => console.error("[useApi]", ...args),
};
/* eslint-enable no-console */

export function useApi<T>(fetcher: () => Promise<T>, deps: unknown[] = []): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  const refetch = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    hookLog.info("Fetching data... (deps changed or refetch triggered)");

    fetcher()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);

          // Log data shape for debugging
          if (result && typeof result === "object") {
            const obj = result as Record<string, unknown>;
            if ("entries" in obj && Array.isArray(obj.entries)) {
              const count = (obj.entries as unknown[]).length;
              if (count === 0) {
                hookLog.warn(
                  "Received EMPTY data (0 entries) — " +
                    "UI will show empty table. " +
                    "Check backend logs for details.",
                );
              } else {
                hookLog.info(`Received ${count} entries`);
              }
            } else if ("count" in obj && obj.count === 0) {
              hookLog.warn(
                "Received EMPTY data (count=0) — " +
                  "UI will show empty content.",
              );
            }
          }
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const error = err instanceof Error ? err : new Error(String(err));
          hookLog.error("Fetch failed:", error.message);
          setError(error);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey, ...deps]);

  return { data, error, loading, refetch };
}
