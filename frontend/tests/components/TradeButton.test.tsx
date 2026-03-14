import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TradeButton } from "@/components/affiliate/TradeButton";

describe("TradeButton", () => {
  it("renders nothing when ticker is null", () => {
    const { container } = render(<TradeButton ticker={null} companySlug="ionq" />);
    expect(container.innerHTML).toBe("");
  });

  it("renders trade buttons for each broker", () => {
    render(<TradeButton ticker="IONQ" companySlug="ionq" />);
    expect(screen.getByTestId("trade-button")).toBeInTheDocument();
    expect(screen.getByTestId("trade-link-ibkr")).toBeInTheDocument();
    expect(screen.getByTestId("trade-link-etoro")).toBeInTheDocument();
  });

  it("displays the ticker in the heading", () => {
    render(<TradeButton ticker="QBTS" companySlug="d-wave" />);
    expect(screen.getByText("Trade QBTS")).toBeInTheDocument();
  });

  it("includes FTC disclosure notice", () => {
    render(<TradeButton ticker="RGTI" companySlug="rigetti" />);
    expect(screen.getByText(/Affiliate links/)).toBeInTheDocument();
  });

  it("generates tracked affiliate links with correct params", () => {
    render(<TradeButton ticker="IONQ" companySlug="ionq" />);
    const link = screen.getByTestId("trade-link-ibkr");
    expect(link.getAttribute("href")).toContain("broker=ibkr");
    expect(link.getAttribute("href")).toContain("ticker=IONQ");
    expect(link.getAttribute("href")).toContain("company=ionq");
  });

  it("sets rel=sponsored for affiliate compliance", () => {
    render(<TradeButton ticker="IONQ" companySlug="ionq" />);
    const link = screen.getByTestId("trade-link-ibkr");
    expect(link.getAttribute("rel")).toContain("sponsored");
  });
});
