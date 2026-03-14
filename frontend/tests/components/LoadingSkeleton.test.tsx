import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { TableSkeleton, ChartSkeleton, CardSkeleton } from "@/components/ui/LoadingSkeleton";

describe("LoadingSkeleton", () => {
  it("renders TableSkeleton with default rows", () => {
    const { container } = render(<TableSkeleton />);
    const animatedDivs = container.querySelectorAll(".animate-pulse > div");
    expect(animatedDivs.length).toBe(11); // 1 header + 10 rows
  });

  it("renders TableSkeleton with custom rows", () => {
    const { container } = render(<TableSkeleton rows={5} />);
    const animatedDivs = container.querySelectorAll(".animate-pulse > div");
    expect(animatedDivs.length).toBe(6); // 1 header + 5 rows
  });

  it("renders ChartSkeleton", () => {
    const { container } = render(<ChartSkeleton />);
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });

  it("renders CardSkeleton", () => {
    const { container } = render(<CardSkeleton />);
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });
});
