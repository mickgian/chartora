import { ImageResponse } from "next/og";
import type { NextRequest } from "next/server";

export const dynamic = "force-static";
export const runtime = "edge";

const CARD_WIDTH = 1200;
const CARD_HEIGHT = 630;

export async function GET(request: NextRequest): Promise<ImageResponse> {
  const { searchParams } = request.nextUrl;
  const title = searchParams.get("title") ?? "Quantum Computing Company Rankings";
  const subtitle = searchParams.get("subtitle") ?? "Live leaderboard powered by data";
  const score = searchParams.get("score");
  const type = searchParams.get("type") ?? "leaderboard";

  const badgeText =
    type === "company"
      ? "Company Analysis"
      : type === "ranking"
        ? "Metric Rankings"
        : "Leaderboard";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "60px 80px",
          background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%)",
          fontFamily: "sans-serif",
          color: "white",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            marginBottom: "24px",
          }}
        >
          <div
            style={{
              fontSize: "36px",
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>&#9883;</span>
            <span>Chartora</span>
          </div>
          <div
            style={{
              fontSize: "14px",
              fontWeight: 600,
              background: "rgba(255,255,255,0.2)",
              padding: "4px 12px",
              borderRadius: "9999px",
              display: "flex",
            }}
          >
            {badgeText}
          </div>
        </div>

        <div
          style={{
            fontSize: "56px",
            fontWeight: 800,
            lineHeight: 1.1,
            marginBottom: "16px",
            display: "flex",
            maxWidth: "900px",
          }}
        >
          {title}
        </div>

        <div
          style={{
            fontSize: "24px",
            opacity: 0.85,
            marginBottom: "32px",
            display: "flex",
          }}
        >
          {subtitle}
        </div>

        {score && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
            }}
          >
            <div
              style={{
                fontSize: "20px",
                fontWeight: 600,
                background: "rgba(255,255,255,0.15)",
                padding: "8px 20px",
                borderRadius: "12px",
                display: "flex",
              }}
            >
              Quantum Power Score: {score}
            </div>
          </div>
        )}

        <div
          style={{
            position: "absolute",
            bottom: "40px",
            right: "80px",
            fontSize: "18px",
            opacity: 0.7,
            display: "flex",
          }}
        >
          chartora.com
        </div>
      </div>
    ),
    { width: CARD_WIDTH, height: CARD_HEIGHT },
  );
}
