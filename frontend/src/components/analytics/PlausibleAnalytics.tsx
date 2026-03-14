"use client";

import Script from "next/script";

interface PlausibleAnalyticsProps {
  domain?: string;
  scriptUrl?: string;
}

export function PlausibleAnalytics({
  domain = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN ?? "",
  scriptUrl = process.env.NEXT_PUBLIC_PLAUSIBLE_SCRIPT_URL ?? "https://plausible.io/js/script.js",
}: PlausibleAnalyticsProps) {
  if (!domain) return null;

  return (
    <Script
      defer
      data-domain={domain}
      src={scriptUrl}
      strategy="afterInteractive"
    />
  );
}
