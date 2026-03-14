import type { Metadata } from "next";
import { PremiumCheckout } from "@/components/premium/PremiumCheckout";

export const metadata: Metadata = {
  title: "Chartora Pro — Premium Quantum Intelligence",
  description:
    "Unlock historical scores, insider trading alerts, institutional ownership, CSV exports, API access, and an ad-free experience.",
};

export default function ProPage() {
  return <PremiumCheckout />;
}
