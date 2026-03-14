import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ExportButtons } from "@/components/premium/ExportButtons";

describe("ExportButtons", () => {
  it("renders CSV export button", () => {
    render(<ExportButtons />);
    expect(screen.getByText("Export CSV")).toBeInTheDocument();
  });

  it("renders JSON export button", () => {
    render(<ExportButtons />);
    expect(screen.getByText("Export JSON")).toBeInTheDocument();
  });

  it("renders description text", () => {
    render(<ExportButtons />);
    expect(screen.getByText(/Download the current/)).toBeInTheDocument();
  });
});
