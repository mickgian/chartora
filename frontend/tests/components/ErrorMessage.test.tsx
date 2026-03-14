import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

describe("ErrorMessage", () => {
  it("displays the error message", () => {
    render(<ErrorMessage message="Something went wrong" />);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("renders retry button when onRetry provided", () => {
    render(<ErrorMessage message="Error" onRetry={() => {}} />);
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("does not render retry button when onRetry not provided", () => {
    render(<ErrorMessage message="Error" />);
    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
  });

  it("calls onRetry when button clicked", () => {
    const onRetry = vi.fn();
    render(<ErrorMessage message="Error" onRetry={onRetry} />);
    fireEvent.click(screen.getByText("Try again"));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
