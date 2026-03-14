import type { Metadata } from "next";
import { CompanyDetail } from "@/components/company/CompanyDetail";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://chartora.com";

interface CompanyPageProps {
  params: Promise<{ slug: string }>;
}

function slugToName(slug: string): string {
  return slug
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export async function generateMetadata({ params }: CompanyPageProps): Promise<Metadata> {
  const { slug } = await params;
  const name = slugToName(slug);
  const title = `${name} — Quantum Power Score & Analysis`;
  const description = `${name} quantum computing analysis: stock performance, patent filings, qubit milestones, funding rounds, and news sentiment on Chartora.`;
  const url = `${SITE_URL}/company/${slug}`;

  return {
    title,
    description,
    alternates: {
      canonical: url,
    },
    openGraph: {
      type: "article",
      title,
      description,
      url,
      siteName: "Chartora",
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
  };
}

export default async function CompanyPage({ params }: CompanyPageProps) {
  const { slug } = await params;
  const name = slugToName(slug);
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name,
    url: `${SITE_URL}/company/${slug}`,
    description: `Quantum computing analysis and Quantum Power Score for ${name}.`,
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <CompanyDetail slug={slug} />
    </>
  );
}
