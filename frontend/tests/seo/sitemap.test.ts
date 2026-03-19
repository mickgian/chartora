import { describe, expect, it } from "vitest";
import sitemap from "@/app/sitemap";

describe("sitemap", () => {
  it("returns a non-empty array of sitemap entries", () => {
    const entries = sitemap();
    expect(entries.length).toBeGreaterThan(0);
  });

  it("includes the homepage with priority 1.0", () => {
    const entries = sitemap();
    const home = entries.find((e) => e.url === "https://chartora.com");
    expect(home).toBeDefined();
    expect(home!.priority).toBe(1.0);
    expect(home!.changeFrequency).toBe("daily");
  });

  it("includes company pages with correct URL pattern", () => {
    const entries = sitemap();
    const companyPages = entries.filter((e) => e.url.includes("/company/"));
    expect(companyPages.length).toBe(24);
    companyPages.forEach((page) => {
      expect(page.url).toMatch(/^https:\/\/chartora\.com\/company\/[\w-]+$/);
      expect(page.priority).toBe(0.8);
    });
  });

  it("includes ranking pages for all metrics", () => {
    const entries = sitemap();
    const rankingPages = entries.filter((e) => e.url.includes("/rankings/"));
    expect(rankingPages.length).toBe(4);
    expect(rankingPages.map((p) => p.url)).toEqual(
      expect.arrayContaining([
        "https://chartora.com/rankings/stock-performance",
        "https://chartora.com/rankings/patents",
        "https://chartora.com/rankings/funding",
        "https://chartora.com/rankings/sentiment",
      ]),
    );
    rankingPages.forEach((page) => {
      expect(page.priority).toBe(0.7);
    });
  });

  it("all entries have lastModified date", () => {
    const entries = sitemap();
    entries.forEach((entry) => {
      expect(entry.lastModified).toBeInstanceOf(Date);
    });
  });
});
