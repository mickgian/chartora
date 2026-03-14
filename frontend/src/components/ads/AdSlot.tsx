"use client";

import { useEffect, useRef } from "react";
import { useAuth } from "@/components/auth/AuthProvider";

export type AdFormat = "auto" | "horizontal" | "vertical" | "rectangle";

export type AdPlacement = "sidebar" | "between-sections" | "footer" | "leaderboard";

interface AdSlotProps {
  adSlot: string;
  adFormat?: AdFormat;
  placement: AdPlacement;
  className?: string;
}

const PLACEMENT_STYLES: Record<AdPlacement, string> = {
  sidebar: "min-h-[250px] w-full",
  "between-sections": "min-h-[90px] w-full",
  footer: "min-h-[90px] w-full",
  leaderboard: "min-h-[90px] w-full",
};

declare global {
  interface Window {
    adsbygoogle?: Record<string, unknown>[];
  }
}

/**
 * Renders a Google AdSense ad unit.
 * Hidden when the user has a premium subscription (detected via auth context).
 */
export function AdSlot({ adSlot, adFormat = "auto", placement, className = "" }: AdSlotProps) {
  const adRef = useRef<HTMLModElement>(null);
  const pushed = useRef(false);
  const { user } = useAuth();

  const isPremium =
    user?.is_premium ||
    (typeof document !== "undefined" && document.documentElement.dataset.premium === "true");

  useEffect(() => {
    if (isPremium || pushed.current) return;
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
      pushed.current = true;
    } catch {
      // AdSense not loaded or blocked — silently ignore
    }
  }, [isPremium]);

  if (isPremium) return null;

  return (
    <div
      className={`ad-container flex items-center justify-center overflow-hidden ${PLACEMENT_STYLES[placement]} ${className}`}
      data-testid={`ad-slot-${placement}`}
      aria-label="Advertisement"
    >
      <ins
        ref={adRef}
        className="adsbygoogle"
        style={{ display: "block" }}
        data-ad-client={process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID ?? ""}
        data-ad-slot={adSlot}
        data-ad-format={adFormat}
        data-full-width-responsive="true"
      />
    </div>
  );
}
