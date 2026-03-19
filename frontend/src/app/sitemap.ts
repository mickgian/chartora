import type { MetadataRoute } from "next";
import type { RankingMetric } from "@/types/api";

export const dynamic = "force-static";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://chartora.com";

const COMPANY_SLUGS = [
  "ionq",
  "d-wave-quantum",
  "rigetti-computing",
  "quantum-computing-inc",
  "arqit-quantum",
  "infleqtion",
  "sealsq",
  "btq-technologies",
  "quantumctek",
  "quantum-emotion",
  "01-communique",
  "ibm",
  "alphabet-google",
  "microsoft",
  "amazon-aws",
  "intel",
  "honeywell-quantinuum",
  "nvidia",
  "fujitsu",
  "defiance-quantum-etf",
  "wisdomtree-quantum-etf",
  "vaneck-quantum-etf",
  "ishares-quantum-etf",
  "globalx-ai-quantum-etf",
];

const RANKING_METRICS: RankingMetric[] = ["stock-performance", "patents", "funding", "sentiment"];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  const staticPages: MetadataRoute.Sitemap = [
    {
      url: SITE_URL,
      lastModified: now,
      changeFrequency: "daily",
      priority: 1.0,
    },
    {
      url: `${SITE_URL}/methodology`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.6,
    },
    {
      url: `${SITE_URL}/about`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.5,
    },
    {
      url: `${SITE_URL}/changelog`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 0.4,
    },
  ];

  const companyPages: MetadataRoute.Sitemap = COMPANY_SLUGS.map((slug) => ({
    url: `${SITE_URL}/company/${slug}`,
    lastModified: now,
    changeFrequency: "daily" as const,
    priority: 0.8,
  }));

  const rankingPages: MetadataRoute.Sitemap = RANKING_METRICS.map((metric) => ({
    url: `${SITE_URL}/rankings/${metric}`,
    lastModified: now,
    changeFrequency: "daily" as const,
    priority: 0.7,
  }));

  return [...staticPages, ...companyPages, ...rankingPages];
}
