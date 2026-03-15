import type { Metadata } from "next";
import { CompanyDetail } from "@/components/company/CompanyDetail";
import { ShareButtons } from "@/components/sharing/ShareButtons";
import { ALL_COMPANY_SLUGS } from "@/lib/mock-data";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://chartora.com";

export function generateStaticParams() {
  return ALL_COMPANY_SLUGS.map((slug) => ({ slug }));
}

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
  const ogImage = `${SITE_URL}/api/og?title=${encodeURIComponent(name)}&type=company&subtitle=${encodeURIComponent("Quantum Power Score & Analysis")}`;

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
      images: [{ url: ogImage, width: 1200, height: 630, alt: title }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [ogImage],
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

  const pageUrl = `${SITE_URL}/company/${slug}`;
  const pageDescription = `Quantum computing analysis and Quantum Power Score for ${name}.`;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <CompanyDetail slug={slug} />
      <div className="mt-8 flex justify-end">
        <ShareButtons url={pageUrl} title={`${name} — Quantum Power Score`} description={pageDescription} />
      </div>
    </>
  );
}
