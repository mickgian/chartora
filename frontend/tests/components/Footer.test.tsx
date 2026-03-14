import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Footer } from "@/components/layout/Footer";

describe("Footer", () => {
  it("renders Chartora branding", () => {
    render(<Footer />);
    expect(screen.getByText("Chartora")).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    render(<Footer />);
    expect(screen.getByText("Leaderboard")).toBeInTheDocument();
    expect(screen.getByText("Rankings")).toBeInTheDocument();
  });

  it("renders data attribution", () => {
    render(<Footer />);
    expect(screen.getByText(/Data sourced from/)).toBeInTheDocument();
  });
});
