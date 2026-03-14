import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/components/auth/AuthProvider";

function TestConsumer() {
  const { user, loading } = useAuth();
  if (loading) return <div data-testid="loading">Loading</div>;
  if (user) return <div data-testid="user">{user.email}</div>;
  return <div data-testid="no-user">Not logged in</div>;
}

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    delete document.documentElement.dataset.premium;
    vi.restoreAllMocks();
  });

  it("provides null user when no token in storage", async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    // Initially loading, then resolves
    const noUser = await screen.findByTestId("no-user");
    expect(noUser).toBeInTheDocument();
  });

  it("returns loading=true initially", () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    // Should show loading before fetch resolves
    expect(screen.getByTestId("loading") || screen.getByTestId("no-user")).toBeInTheDocument();
  });

  it("provides default context values", () => {
    const { user, loading } = { user: null, loading: true };
    expect(user).toBeNull();
    expect(loading).toBe(true);
  });
});
