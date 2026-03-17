import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiClient, ApiError } from "@/lib/api-client";

const mockFetch = vi.fn();
global.fetch = mockFetch;

function jsonResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Error",
    json: () => Promise.resolve(data),
    headers: new Headers({ "content-length": "100" }),
  };
}

describe("apiClient", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("getLeaderboard", () => {
    it("fetches leaderboard without params", async () => {
      const mockData = { metric: "total_score", entries: [], count: 0, updated_at: null };
      mockFetch.mockResolvedValueOnce(jsonResponse(mockData));

      const result = await apiClient.getLeaderboard();

      expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/v1/leaderboard");
      expect(result).toEqual(mockData);
    });

    it("passes sort_by and limit params", async () => {
      const mockData = { metric: "patent_velocity", entries: [], count: 0, updated_at: null };
      mockFetch.mockResolvedValueOnce(jsonResponse(mockData));

      await apiClient.getLeaderboard({ sort_by: "patent_velocity", limit: 5 });

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("sort_by=patent_velocity");
      expect(url).toContain("limit=5");
    });
  });

  describe("getCompany", () => {
    it("fetches company by slug", async () => {
      const mockData = { company: { id: 1, name: "IonQ", slug: "ionq" }, score: null };
      mockFetch.mockResolvedValueOnce(jsonResponse(mockData));

      const result = await apiClient.getCompany("ionq");

      expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/v1/companies/ionq");
      expect(result).toEqual(mockData);
    });
  });

  describe("getStockHistory", () => {
    it("fetches stock history with days param", async () => {
      const mockData = { company_slug: "ionq", prices: [], count: 0 };
      mockFetch.mockResolvedValueOnce(jsonResponse(mockData));

      await apiClient.getStockHistory("ionq", 30);

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/companies/ionq/stock?days=30",
      );
    });

    it("defaults to 90 days", async () => {
      mockFetch.mockResolvedValueOnce(jsonResponse({ company_slug: "ionq", prices: [], count: 0 }));

      await apiClient.getStockHistory("ionq");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/companies/ionq/stock?days=90",
      );
    });

    it("omits days param when days is 0 (ALL)", async () => {
      mockFetch.mockResolvedValueOnce(jsonResponse({ company_slug: "ionq", prices: [], count: 0 }));

      await apiClient.getStockHistory("ionq", 0);

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/companies/ionq/stock",
        { cache: "no-store" },
      );
    });
  });

  describe("getIntradayHistory", () => {
    it("fetches intraday data for a company", async () => {
      const mockData = { company_slug: "ionq", prices: [], count: 0 };
      mockFetch.mockResolvedValueOnce(jsonResponse(mockData));

      await apiClient.getIntradayHistory("ionq");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/companies/ionq/stock/intraday",
        { cache: "no-store" },
      );
    });
  });

  describe("getPatents", () => {
    it("fetches patents for a company", async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({ company_slug: "ionq", patents: [], count: 0 }),
      );

      await apiClient.getPatents("ionq");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/companies/ionq/patents",
      );
    });
  });

  describe("getNews", () => {
    it("fetches news with limit param", async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({ company_slug: "ionq", articles: [], count: 0 }),
      );

      await apiClient.getNews("ionq", 10);

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/companies/ionq/news?limit=10",
      );
    });
  });

  describe("getFilings", () => {
    it("fetches filings for a company", async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({ company_slug: "ionq", filings: [], count: 0 }),
      );

      await apiClient.getFilings("ionq");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/v1/companies/ionq/filings",
      );
    });
  });

  describe("getRanking", () => {
    it("fetches ranking by metric", async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({ metric: "patent_velocity", entries: [], count: 0 }),
      );

      await apiClient.getRanking("patents");

      expect(mockFetch).toHaveBeenCalledWith("http://localhost:8000/api/v1/rankings/patents");
    });
  });

  describe("error handling", () => {
    it("throws ApiError on 404", async () => {
      mockFetch.mockResolvedValue(jsonResponse({ detail: "Company not found" }, 404));

      await expect(apiClient.getCompany("nonexistent")).rejects.toThrow(ApiError);
    });

    it("retries on 500 errors", async () => {
      mockFetch
        .mockResolvedValueOnce(jsonResponse({ detail: "Server error" }, 500))
        .mockResolvedValueOnce(jsonResponse({ detail: "Server error" }, 500))
        .mockResolvedValueOnce(jsonResponse({ detail: "Server error" }, 500));

      await expect(apiClient.getCompany("ionq")).rejects.toThrow(ApiError);
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });

    it("retries on network errors", async () => {
      mockFetch
        .mockRejectedValueOnce(new TypeError("Failed to fetch"))
        .mockRejectedValueOnce(new TypeError("Failed to fetch"))
        .mockRejectedValueOnce(new TypeError("Failed to fetch"));

      await expect(apiClient.getCompany("ionq")).rejects.toThrow("Failed to fetch");
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });
  });
});
