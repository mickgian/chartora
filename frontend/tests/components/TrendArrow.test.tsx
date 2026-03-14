import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TrendArrow } from "@/components/leaderboard/TrendArrow";

describe("TrendArrow", () => {
  it("renders green arrow for up trend", () => {
    const { container } = render(<TrendArrow trend="up" />);
    const span = container.querySelector("span");
    expect(span?.className).toContain("text-green-600");
  });

  it("renders red arrow for down trend", () => {
    const { container } = render(<TrendArrow trend="down" />);
    const span = container.querySelector("span");
    expect(span?.className).toContain("text-red-600");
  });

  it("renders gray dash for flat trend", () => {
    const { container } = render(<TrendArrow trend="flat" />);
    const span = container.querySelector("span");
    expect(span?.className).toContain("text-gray-400");
  });

  it("shows rank change number when provided", () => {
    render(<TrendArrow trend="up" rankChange={3} />);
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("does not show rank change number for zero", () => {
    const { container } = render(<TrendArrow trend="up" rankChange={0} />);
    expect(container.querySelectorAll("span").length).toBe(1);
  });
});
