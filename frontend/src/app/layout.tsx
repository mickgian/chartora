import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "@/components/layout/ThemeProvider";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { PlausibleAnalytics } from "@/components/analytics/PlausibleAnalytics";
import { AdSenseScript } from "@/components/ads/AdSenseScript";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://chartora.com";

export const metadata: Metadata = {
  title: {
    default: "Chartora — Quantum Computing Company Rankings",
    template: "%s | Chartora",
  },
  description:
    "Live leaderboard ranking quantum computing companies by Quantum Power Score — combining stock performance, patents, qubits, funding, and sentiment.",
  metadataBase: new URL(SITE_URL),
  openGraph: {
    type: "website",
    siteName: "Chartora",
    title: "Chartora — Quantum Computing Company Rankings",
    description:
      "Live leaderboard ranking quantum computing companies by Quantum Power Score — combining stock performance, patents, qubits, funding, and sentiment.",
    url: SITE_URL,
    locale: "en_US",
    images: [
      {
        url: `${SITE_URL}/api/og?title=Quantum+Computing+Company+Rankings&type=leaderboard`,
        width: 1200,
        height: 630,
        alt: "Chartora — Quantum Computing Company Rankings",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Chartora — Quantum Computing Company Rankings",
    description:
      "Live leaderboard ranking quantum computing companies by Quantum Power Score.",
    images: [
      `${SITE_URL}/api/og?title=Quantum+Computing+Company+Rankings&type=leaderboard`,
    ],
  },
  alternates: {
    canonical: SITE_URL,
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-snippet": -1,
      "max-image-preview": "large",
      "max-video-preview": -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <PlausibleAnalytics />
        <AdSenseScript />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <ThemeProvider>
          <AuthProvider>
            <div className="flex min-h-screen flex-col">
              <Header />
              <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8">{children}</main>
              <Footer />
            </div>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
