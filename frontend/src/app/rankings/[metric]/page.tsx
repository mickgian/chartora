import type { Metadata } from "next";
import { MetricDeepDive } from "@/components/rankings/MetricDeepDive";
import { ShareButtons } from "@/components/sharing/ShareButtons";
import { EmbedCodeGenerator } from "@/components/sharing/EmbedCodeGenerator";
import type { RankingMetric } from "@/types/api";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://chartora.com";

const VALID_METRICS: RankingMetric[] = ["stock-performance", "patents", "funding", "sentiment"];

export function generateStaticParams() {
  return VALID_METRICS.map((metric) => ({ metric }));
}

const METRIC_META: Record<RankingMetric, { title: string; description: string }> = {
  "stock-performance": {
    title: "Stock Performance Rankings",
    description:
      "Quantum computing companies ranked by stock momentum — 30, 60, and 90 day price performance.",
  },
  patents: {
    title: "Patent Activity Rankings",
    description:
      "Quantum computing companies ranked by patent filing velocity over the last 12 months.",
  },
  funding: {
    title: "Funding Rankings",
    description:
      "Quantum computing companies ranked by total funding raised and recent investment rounds.",
  },
  sentiment: {
    title: "News Sentiment Rankings",
    description:
      "Quantum computing companies ranked by AI-scored news sentiment from recent media coverage.",
  },
};

interface MetricPageProps {
  params: Promise<{ metric: string }>;
}

export async function generateMetadata({ params }: MetricPageProps): Promise<Metadata> {
  const { metric } = await params;
  const meta = METRIC_META[metric as RankingMetric];
  if (!meta) {
    return { title: "Rankings" };
  }
  const url = `${SITE_URL}/rankings/${metric}`;
  const ogImage = `${SITE_URL}/api/og?title=${encodeURIComponent(meta.title)}&type=ranking&subtitle=${encodeURIComponent(meta.description)}`;
  return {
    title: meta.title,
    description: meta.description,
    alternates: {
      canonical: url,
    },
    openGraph: {
      type: "website",
      title: meta.title,
      description: meta.description,
      url,
      siteName: "Chartora",
      images: [{ url: ogImage, width: 1200, height: 630, alt: meta.title }],
    },
    twitter: {
      card: "summary_large_image",
      title: meta.title,
      description: meta.description,
      images: [ogImage],
    },
  };
}

export default async function MetricPage({ params }: MetricPageProps) {
  const { metric } = await params;
  if (!VALID_METRICS.includes(metric as RankingMetric)) {
    return (
      <div className="py-12 text-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Invalid metric</h1>
        <p className="mt-2 text-gray-500 dark:text-slate-400">
          Valid metrics: {VALID_METRICS.join(", ")}
        </p>
      </div>
    );
  }

  const meta = METRIC_META[metric as RankingMetric];
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: meta.title,
    description: meta.description,
    url: `${SITE_URL}/rankings/${metric}`,
  };

  const pageUrl = `${SITE_URL}/rankings/${metric}`;
  const embedUrl = `${SITE_URL}/rankings/${metric}?embed=true`;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <MetricDeepDive metric={metric as RankingMetric} />
      <div className="mt-8 flex flex-col gap-6">
        <div className="flex justify-end">
          <ShareButtons url={pageUrl} title={meta.title} description={meta.description} />
        </div>
        <EmbedCodeGenerator chartUrl={embedUrl} title={meta.title} />
      </div>
    </>
  );
}
