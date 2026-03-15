import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ShareButtons } from "@/components/sharing/ShareButtons";

describe("ShareButtons", () => {
  const defaultProps = {
    url: "https://chartora.com/company/ionq",
    title: "IonQ — Quantum Power Score",
    description: "Quantum computing analysis for IonQ",
  };

  it("renders share label", () => {
    render(<ShareButtons {...defaultProps} />);
    expect(screen.getByText("Share:")).toBeInTheDocument();
  });

  it("renders Twitter/X share link", () => {
    render(<ShareButtons {...defaultProps} />);
    const twitterLink = screen.getByLabelText(/Twitter/);
    expect(twitterLink).toBeInTheDocument();
    expect(twitterLink).toHaveAttribute("href");
    expect(twitterLink.getAttribute("href")).toContain("twitter.com/intent/tweet");
    expect(twitterLink).toHaveAttribute("target", "_blank");
    expect(twitterLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders LinkedIn share link", () => {
    render(<ShareButtons {...defaultProps} />);
    const linkedInLink = screen.getByLabelText(/LinkedIn/);
    expect(linkedInLink).toBeInTheDocument();
    expect(linkedInLink.getAttribute("href")).toContain("linkedin.com/sharing");
  });

  it("renders copy link button", () => {
    render(<ShareButtons {...defaultProps} />);
    const copyButton = screen.getByLabelText("Copy link to clipboard");
    expect(copyButton).toBeInTheDocument();
  });

  it("encodes URL in share links", () => {
    render(<ShareButtons {...defaultProps} />);
    const twitterLink = screen.getByLabelText(/Twitter/);
    expect(twitterLink.getAttribute("href")).toContain(
      encodeURIComponent(defaultProps.url),
    );
  });
});
