import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Header } from "@/components/layout/Header";
import { ThemeProvider } from "@/components/layout/ThemeProvider";

function renderHeader() {
  return render(
    <ThemeProvider>
      <Header />
    </ThemeProvider>,
  );
}

describe("Header", () => {
  it("renders Chartora branding", () => {
    renderHeader();
    expect(screen.getByText("Chartora")).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    renderHeader();
    expect(screen.getByText("Leaderboard")).toBeInTheDocument();
    expect(screen.getByText("Stock")).toBeInTheDocument();
    expect(screen.getByText("Patents")).toBeInTheDocument();
    expect(screen.getByText("Funding")).toBeInTheDocument();
    expect(screen.getByText("Sentiment")).toBeInTheDocument();
  });

  it("renders theme toggle button", () => {
    renderHeader();
    const themeButton = screen.getByLabelText(/Switch to/);
    expect(themeButton).toBeInTheDocument();
  });

  it("toggles mobile menu", () => {
    renderHeader();
    const menuButton = screen.getByLabelText("Toggle menu");
    fireEvent.click(menuButton);
    // Mobile menu should now show duplicate nav links
    const leaderboardLinks = screen.getAllByText("Leaderboard");
    expect(leaderboardLinks.length).toBeGreaterThan(1);
  });
});
