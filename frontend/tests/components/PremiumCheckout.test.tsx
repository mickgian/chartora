import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PremiumCheckout } from "@/components/premium/PremiumCheckout";

describe("PremiumCheckout", () => {
  it("renders the page heading", () => {
    render(<PremiumCheckout />);
    expect(screen.getByText("Chartora Pro")).toBeInTheDocument();
  });

  it("renders the price", () => {
    render(<PremiumCheckout />);
    expect(screen.getByText("$9")).toBeInTheDocument();
  });

  it("renders the checkout button", () => {
    render(<PremiumCheckout />);
    const button = screen.getByTestId("checkout-button");
    expect(button).toBeInTheDocument();
    expect(button.textContent).toContain("Subscribe");
  });

  it("renders an email input field", () => {
    render(<PremiumCheckout />);
    expect(screen.getByLabelText("Email address")).toBeInTheDocument();
  });

  it("lists premium features", () => {
    render(<PremiumCheckout />);
    expect(screen.getByText("Ad-free experience")).toBeInTheDocument();
    expect(screen.getByText("REST API access")).toBeInTheDocument();
    expect(screen.getByText(/CSV & JSON data export/)).toBeInTheDocument();
  });

  it("renders Stripe attribution", () => {
    render(<PremiumCheckout />);
    expect(screen.getByText(/Payments processed securely by Stripe/)).toBeInTheDocument();
  });
});
