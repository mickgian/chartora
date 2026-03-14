import { describe, it, expect } from "vitest";
import { getBrokers, generateAffiliateLink, buildTrackedAffiliateLink } from "@/lib/affiliate";

describe("affiliate", () => {
  describe("getBrokers", () => {
    it("returns at least two brokers", () => {
      const brokers = getBrokers();
      expect(brokers.length).toBeGreaterThanOrEqual(2);
    });

    it("each broker has required fields", () => {
      for (const broker of getBrokers()) {
        expect(broker.name).toBeTruthy();
        expect(broker.slug).toBeTruthy();
        expect(broker.baseUrl).toBeTruthy();
        expect(broker.urlTemplate).toContain("{ticker}");
      }
    });
  });

  describe("generateAffiliateLink", () => {
    it("returns null when ticker is null", () => {
      const brokers = getBrokers();
      expect(generateAffiliateLink(brokers[0], null)).toBeNull();
    });

    it("replaces {ticker} in the URL template", () => {
      const brokers = getBrokers();
      const link = generateAffiliateLink(brokers[0], "IONQ");
      expect(link).not.toBeNull();
      expect(link).toContain("IONQ");
      expect(link).not.toContain("{ticker}");
    });

    it("encodes special characters in ticker", () => {
      const brokers = getBrokers();
      const link = generateAffiliateLink(brokers[0], "A&B");
      expect(link).toContain("A%26B");
    });
  });

  describe("buildTrackedAffiliateLink", () => {
    it("builds a tracking URL with all params", () => {
      const url = buildTrackedAffiliateLink("ibkr", "IONQ", "ionq");
      expect(url).toBe("/api/affiliate/click?broker=ibkr&ticker=IONQ&company=ionq");
    });
  });
});
