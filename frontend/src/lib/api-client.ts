/**
 * API client for the Chartora backend.
 * Provides typed fetch wrappers with error handling and retries.
 *
 * In demo mode (NEXT_PUBLIC_DEMO_MODE=true), returns mock data instead
 * of calling the backend. Used for GitHub Pages static preview.
 */

import type {
  CompanyDetailResponse,
  FilingListResponse,
  GovernmentContractListResponse,
  HistoricalScoresResponse,
  InsiderTradingResponse,
  InstitutionalOwnershipResponse,
  IntradayResponse,
  LeaderboardResponse,
  NewsListResponse,
  PatentListResponse,
  RankingMetric,
  RankingResponse,
  RdSpendingResponse,
  SortableMetric,
  StockHistoryResponse,
} from "@/types/api";
import { mockApi } from "@/lib/mock-data";

const IS_DEMO = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public detail?: string,
  ) {
    super(detail ?? `API error: ${status} ${statusText}`);
    this.name = "ApiError";
  }
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

const log = {
  info: (...args: unknown[]) => console.log("[Chartora API]", ...args), // eslint-disable-line no-console
  warn: (...args: unknown[]) => console.warn("[Chartora API]", ...args), // eslint-disable-line no-console
  error: (...args: unknown[]) => console.error("[Chartora API]", ...args), // eslint-disable-line no-console
};

// Log config on first load
log.info(
  `Initialized — BASE_URL=${BASE_URL}, DEMO_MODE=${IS_DEMO}`,
);

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchWithRetry(url: string, retries = MAX_RETRIES): Promise<Response> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      log.info(`[FETCH] ${url} (attempt ${attempt + 1}/${retries + 1})`);
      const response = await fetch(url, { cache: "no-store" });

      if (response.ok) {
        log.info(
          `[FETCH] ${url} -> ${response.status} (${response.headers.get("content-length") ?? "?"} bytes)`,
        );
        return response;
      }

      log.warn(
        `[FETCH] ${url} -> ${response.status} ${response.statusText}`,
      );

      if (response.status >= 500 && attempt < retries) {
        log.warn(
          `[FETCH] Server error, retrying in ${RETRY_DELAY_MS * (attempt + 1)}ms...`,
        );
        await sleep(RETRY_DELAY_MS * (attempt + 1));
        continue;
      }

      let detail: string | undefined;
      try {
        const body = await response.json();
        detail = body.detail;
      } catch {
        // ignore parse errors
      }
      throw new ApiError(response.status, response.statusText, detail);
    } catch (error) {
      if (error instanceof ApiError) throw error;

      log.error(
        `[FETCH] Network error for ${url}:`,
        error instanceof Error ? error.message : error,
      );

      if (attempt < retries) {
        log.warn(
          `[FETCH] Retrying in ${RETRY_DELAY_MS * (attempt + 1)}ms...`,
        );
        await sleep(RETRY_DELAY_MS * (attempt + 1));
        continue;
      }
      throw error;
    }
  }

  throw new Error("Unexpected: exhausted retries without result");
}

async function get<T>(path: string): Promise<T> {
  const response = await fetchWithRetry(`${BASE_URL}${path}`);
  const data = (await response.json()) as T;

  // Log response shape for debugging
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    if ("entries" in obj && Array.isArray(obj.entries)) {
      log.info(
        `[DATA] ${path} -> ${(obj.entries as unknown[]).length} entries`,
      );
      if ((obj.entries as unknown[]).length === 0) {
        log.warn(
          `[DATA] ${path} -> EMPTY response (0 entries). ` +
            "Backend may have no data in database.",
        );
      }
    } else if ("count" in obj) {
      log.info(`[DATA] ${path} -> count=${obj.count}`);
      if (obj.count === 0) {
        log.warn(
          `[DATA] ${path} -> EMPTY response (count=0). ` +
            "Backend may have no data in database.",
        );
      }
    }
  }

  return data;
}

export const apiClient = {
  getLeaderboard(params?: {
    sort_by?: SortableMetric;
    limit?: number;
    sector?: "pure_play" | "big_tech" | "etf";
  }): Promise<LeaderboardResponse> {
    if (IS_DEMO) return Promise.resolve(mockApi.getLeaderboard(params));
    const searchParams = new URLSearchParams();
    if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.sector) searchParams.set("sector", params.sector);
    const qs = searchParams.toString();
    return get(`/api/v1/leaderboard${qs ? `?${qs}` : ""}`);
  },

  getCompany(slug: string): Promise<CompanyDetailResponse> {
    if (IS_DEMO) return Promise.resolve(mockApi.getCompany(slug));
    return get(`/api/v1/companies/${encodeURIComponent(slug)}`);
  },

  getStockHistory(slug: string, days = 90): Promise<StockHistoryResponse> {
    if (IS_DEMO) return Promise.resolve(mockApi.getStockHistory(slug, days));
    const qs = days > 0 ? `?days=${days}` : "";
    return get(`/api/v1/companies/${encodeURIComponent(slug)}/stock${qs}`);
  },

  getIntradayHistory(slug: string): Promise<IntradayResponse> {
    if (IS_DEMO) return Promise.resolve(mockApi.getIntradayHistory(slug));
    return get(`/api/v1/companies/${encodeURIComponent(slug)}/stock/intraday`);
  },

  getPatents(slug: string): Promise<PatentListResponse> {
    if (IS_DEMO) return Promise.resolve(mockApi.getPatents(slug));
    return get(`/api/v1/companies/${encodeURIComponent(slug)}/patents`);
  },

  getNews(slug: string, limit = 20): Promise<NewsListResponse> {
    if (IS_DEMO) return Promise.resolve(mockApi.getNews(slug));
    return get(`/api/v1/companies/${encodeURIComponent(slug)}/news?limit=${limit}`);
  },

  getFilings(slug: string): Promise<FilingListResponse> {
    if (IS_DEMO) return Promise.resolve(mockApi.getFilings(slug));
    return get(`/api/v1/companies/${encodeURIComponent(slug)}/filings`);
  },

  getRanking(metric: RankingMetric): Promise<RankingResponse> {
    if (IS_DEMO) return Promise.resolve(mockApi.getRanking(metric));
    return get(`/api/v1/rankings/${encodeURIComponent(metric)}`);
  },

  // Premium endpoints (require auth token)
  getHistoricalScores(slug: string, days = 365): Promise<HistoricalScoresResponse> {
    return get(`/api/v1/pro/historical-scores/${encodeURIComponent(slug)}?days=${days}`);
  },

  getFullPatentHistory(slug: string): Promise<{ company_slug: string; company_name: string; patents: unknown[]; count: number }> {
    return get(`/api/v1/pro/patents/${encodeURIComponent(slug)}/full-history`);
  },

  getInsiderTrading(slug: string): Promise<InsiderTradingResponse> {
    return get(`/api/v1/pro/insider-trading/${encodeURIComponent(slug)}`);
  },

  getInstitutionalOwnership(slug: string): Promise<InstitutionalOwnershipResponse> {
    return get(`/api/v1/pro/institutional-ownership/${encodeURIComponent(slug)}`);
  },

  getRdSpending(slug: string): Promise<RdSpendingResponse> {
    return get(`/api/v1/pro/rd-spending/${encodeURIComponent(slug)}`);
  },

  getGovernmentContracts(slug: string): Promise<GovernmentContractListResponse> {
    return get(`/api/v1/pro/government-contracts/${encodeURIComponent(slug)}`);
  },

  getGovernmentContractRankings(): Promise<RankingResponse> {
    return get("/api/v1/rankings/government-contracts");
  },
};
