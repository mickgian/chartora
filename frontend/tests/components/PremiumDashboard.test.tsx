import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// Mock AuthProvider to control user state
vi.mock("@/components/auth/AuthProvider", () => ({
  useAuth: () => ({
    user: { id: 1, email: "pro@example.com", is_premium: true },
    loading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import { PremiumDashboard } from "@/components/premium/PremiumDashboard";

describe("PremiumDashboard", () => {
  it("renders dashboard title", () => {
    render(<PremiumDashboard />);
    expect(screen.getByText("Premium Dashboard")).toBeInTheDocument();
  });

  it("shows PRO badge", () => {
    render(<PremiumDashboard />);
    expect(screen.getByText("PRO")).toBeInTheDocument();
  });

  it("shows user email", () => {
    render(<PremiumDashboard />);
    expect(screen.getByText(/pro@example.com/)).toBeInTheDocument();
  });

  it("renders tab navigation", () => {
    render(<PremiumDashboard />);
    expect(screen.getByText("Historical Data")).toBeInTheDocument();
    expect(screen.getByText("Alerts")).toBeInTheDocument();
    expect(screen.getByText("Exports")).toBeInTheDocument();
    expect(screen.getByText("API Keys")).toBeInTheDocument();
  });

  it("switches tabs when clicked", () => {
    render(<PremiumDashboard />);
    fireEvent.click(screen.getByText("Exports"));
    expect(screen.getByText("Export CSV")).toBeInTheDocument();
  });
});
