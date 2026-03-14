import { LeaderboardTable } from "@/components/leaderboard/LeaderboardTable";
import { AdSlot } from "@/components/ads/AdSlot";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://chartora.com";

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "Chartora",
  url: SITE_URL,
  description:
    "Live leaderboard ranking quantum computing companies by Quantum Power Score — combining stock performance, patents, qubits, funding, and sentiment.",
  potentialAction: {
    "@type": "SearchAction",
    target: `${SITE_URL}/company/{slug}`,
    "query-input": "required name=slug",
  },
};

export default function HomePage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <LeaderboardTable />
      <AdSlot adSlot="leaderboard-bottom" placement="between-sections" className="mt-8" />
    </>
  );
}
