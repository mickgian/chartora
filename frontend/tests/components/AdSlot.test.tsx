import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AdSlot } from "@/components/ads/AdSlot";

describe("AdSlot", () => {
  beforeEach(() => {
    // Ensure premium is not set
    delete document.documentElement.dataset.premium;
  });

  it("renders an ad container with correct testid", () => {
    render(<AdSlot adSlot="test-slot" placement="sidebar" />);
    expect(screen.getByTestId("ad-slot-sidebar")).toBeInTheDocument();
  });

  it("renders the adsbygoogle ins element", () => {
    render(<AdSlot adSlot="test-slot" placement="footer" />);
    const container = screen.getByTestId("ad-slot-footer");
    const ins = container.querySelector("ins.adsbygoogle");
    expect(ins).toBeInTheDocument();
  });

  it("sets data-ad-slot attribute on the ins element", () => {
    render(<AdSlot adSlot="12345" placement="leaderboard" />);
    const container = screen.getByTestId("ad-slot-leaderboard");
    const ins = container.querySelector("ins.adsbygoogle");
    expect(ins).toHaveAttribute("data-ad-slot", "12345");
  });

  it("sets aria-label for accessibility", () => {
    render(<AdSlot adSlot="test-slot" placement="sidebar" />);
    expect(screen.getByLabelText("Advertisement")).toBeInTheDocument();
  });

  it("hides ads for premium users", () => {
    document.documentElement.dataset.premium = "true";
    render(<AdSlot adSlot="test-slot" placement="sidebar" />);
    expect(screen.queryByTestId("ad-slot-sidebar")).not.toBeInTheDocument();
  });

  it("applies between-sections placement styles", () => {
    render(<AdSlot adSlot="test-slot" placement="between-sections" />);
    const container = screen.getByTestId("ad-slot-between-sections");
    expect(container.className).toContain("min-h-[90px]");
  });

  it("applies sidebar placement styles", () => {
    render(<AdSlot adSlot="test-slot" placement="sidebar" />);
    const container = screen.getByTestId("ad-slot-sidebar");
    expect(container.className).toContain("min-h-[250px]");
  });

  it("applies custom className", () => {
    render(<AdSlot adSlot="test-slot" placement="footer" className="mt-4" />);
    const container = screen.getByTestId("ad-slot-footer");
    expect(container.className).toContain("mt-4");
  });
});
