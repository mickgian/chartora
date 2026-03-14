import { MetricDeepDive } from "@/components/rankings/MetricDeepDive";
import type { RankingMetric } from "@/types/api";

const VALID_METRICS: RankingMetric[] = ["stock-performance", "patents", "funding", "sentiment"];

const METRIC_TITLES: Record<RankingMetric, string> = {
  "stock-performance": "Stock Performance Rankings",
  patents: "Patent Activity Rankings",
  funding: "Funding Rankings",
  sentiment: "News Sentiment Rankings",
};

interface MetricPageProps {
  params: Promise<{ metric: string }>;
}

export async function generateMetadata({ params }: MetricPageProps) {
  const { metric } = await params;
  const title = METRIC_TITLES[metric as RankingMetric] ?? "Rankings";
  return { title };
}

export default async function MetricPage({ params }: MetricPageProps) {
  const { metric } = await params;
  if (!VALID_METRICS.includes(metric as RankingMetric)) {
    return (
      <div className="py-12 text-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Invalid metric</h1>
        <p className="mt-2 text-gray-500 dark:text-gray-400">
          Valid metrics: {VALID_METRICS.join(", ")}
        </p>
      </div>
    );
  }

  return <MetricDeepDive metric={metric as RankingMetric} />;
}
