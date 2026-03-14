import { describe, expect, it } from "vitest";
import { generateMetadata as generateMetricMetadata } from "@/app/rankings/[metric]/page";
import { generateMetadata as generateCompanyMetadata } from "@/app/company/[slug]/page";

describe("metric page metadata", () => {
  it("generates correct metadata for stock-performance", async () => {
    const meta = await generateMetricMetadata({
      params: Promise.resolve({ metric: "stock-performance" }),
    });
    expect(meta.title).toBe("Stock Performance Rankings");
    expect(meta.description).toContain("stock momentum");
    expect(meta.alternates?.canonical).toBe("https://chartora.com/rankings/stock-performance");
  });

  it("generates correct metadata for patents", async () => {
    const meta = await generateMetricMetadata({
      params: Promise.resolve({ metric: "patents" }),
    });
    expect(meta.title).toBe("Patent Activity Rankings");
    expect(meta.description).toContain("patent filing");
  });

  it("generates correct metadata for funding", async () => {
    const meta = await generateMetricMetadata({
      params: Promise.resolve({ metric: "funding" }),
    });
    expect(meta.title).toBe("Funding Rankings");
  });

  it("generates correct metadata for sentiment", async () => {
    const meta = await generateMetricMetadata({
      params: Promise.resolve({ metric: "sentiment" }),
    });
    expect(meta.title).toBe("News Sentiment Rankings");
  });

  it("returns fallback title for invalid metric", async () => {
    const meta = await generateMetricMetadata({
      params: Promise.resolve({ metric: "invalid" }),
    });
    expect(meta.title).toBe("Rankings");
  });

  it("includes OpenGraph metadata", async () => {
    const meta = await generateMetricMetadata({
      params: Promise.resolve({ metric: "patents" }),
    });
    expect(meta.openGraph).toBeDefined();
    expect(meta.openGraph?.siteName).toBe("Chartora");
    expect(meta.openGraph?.url).toBe("https://chartora.com/rankings/patents");
  });

  it("includes Twitter card metadata", async () => {
    const meta = await generateMetricMetadata({
      params: Promise.resolve({ metric: "patents" }),
    });
    expect(meta.twitter).toBeDefined();
    const twitter = meta.twitter as Record<string, unknown>;
    expect(twitter.card).toBe("summary_large_image");
  });
});

describe("company page metadata", () => {
  it("generates correct metadata for a company slug", async () => {
    const meta = await generateCompanyMetadata({
      params: Promise.resolve({ slug: "ionq" }),
    });
    expect(meta.title).toContain("Ionq");
    expect(meta.description).toContain("Ionq");
    expect(meta.alternates?.canonical).toBe("https://chartora.com/company/ionq");
  });

  it("formats multi-word slugs correctly", async () => {
    const meta = await generateCompanyMetadata({
      params: Promise.resolve({ slug: "d-wave-quantum" }),
    });
    expect(meta.title).toContain("D Wave Quantum");
    expect(meta.description).toContain("D Wave Quantum");
  });

  it("includes OpenGraph metadata for company", async () => {
    const meta = await generateCompanyMetadata({
      params: Promise.resolve({ slug: "ionq" }),
    });
    expect(meta.openGraph).toBeDefined();
    const og = meta.openGraph as Record<string, unknown>;
    expect(og.type).toBe("article");
    expect(og.url).toBe("https://chartora.com/company/ionq");
  });
});
