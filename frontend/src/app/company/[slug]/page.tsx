import { CompanyDetail } from "@/components/company/CompanyDetail";

interface CompanyPageProps {
  params: Promise<{ slug: string }>;
}

export default async function CompanyPage({ params }: CompanyPageProps) {
  const { slug } = await params;
  return <CompanyDetail slug={slug} />;
}
