import { describe, expect, it } from "vitest";
import robots from "@/app/robots";

describe("robots", () => {
  it("returns robots config with rules", () => {
    const config = robots();
    expect(config.rules).toBeDefined();
  });

  it("allows crawling of public pages", () => {
    const config = robots();
    const rules = Array.isArray(config.rules) ? config.rules : [config.rules];
    const mainRule = rules.find((r) => r.userAgent === "*");
    expect(mainRule).toBeDefined();
    expect(mainRule!.allow).toBe("/");
  });

  it("disallows crawling of api and premium routes", () => {
    const config = robots();
    const rules = Array.isArray(config.rules) ? config.rules : [config.rules];
    const mainRule = rules.find((r) => r.userAgent === "*");
    expect(mainRule).toBeDefined();
    expect(mainRule!.disallow).toEqual(expect.arrayContaining(["/api/", "/pro/"]));
  });

  it("includes sitemap URL", () => {
    const config = robots();
    expect(config.sitemap).toBe("https://chartora.com/sitemap.xml");
  });
});
