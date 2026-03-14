import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScoreBadge } from "@/components/leaderboard/ScoreBadge";

describe("ScoreBadge", () => {
  it("displays score value with one decimal", () => {
    render(<ScoreBadge score={75.234} />);
    expect(screen.getByText("75.2")).toBeInTheDocument();
  });

  it("applies green color for high scores", () => {
    const { container } = render(<ScoreBadge score={85} />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("bg-green-100");
  });

  it("applies yellow color for medium scores", () => {
    const { container } = render(<ScoreBadge score={45} />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("bg-yellow-100");
  });

  it("applies red color for low scores", () => {
    const { container } = render(<ScoreBadge score={10} />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("bg-red-100");
  });

  it("renders a progress bar", () => {
    const { container } = render(<ScoreBadge score={50} />);
    const bar = container.querySelector('[style*="width"]');
    expect(bar).toBeTruthy();
    expect(bar?.getAttribute("style")).toContain("50%");
  });
});
