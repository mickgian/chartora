import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { LaunchEmailForm } from "@/components/launch/LaunchEmailForm";

describe("LaunchEmailForm", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders email input and submit button", () => {
    render(<LaunchEmailForm />);
    expect(screen.getByPlaceholderText("you@example.com")).toBeInTheDocument();
    expect(screen.getByText("Get Early Access")).toBeInTheDocument();
  });

  it("shows error for empty email", () => {
    render(<LaunchEmailForm />);
    fireEvent.click(screen.getByText("Get Early Access"));
    expect(screen.getByText("Please enter your email address.")).toBeInTheDocument();
  });

  it("shows error for invalid email", () => {
    render(<LaunchEmailForm />);
    const input = screen.getByPlaceholderText("you@example.com");
    fireEvent.change(input, { target: { value: "notanemail" } });
    const form = input.closest("form")!;
    fireEvent.submit(form);
    expect(screen.getByText("Please enter a valid email address.")).toBeInTheDocument();
  });

  it("shows success message on valid submission", () => {
    render(<LaunchEmailForm />);
    const input = screen.getByPlaceholderText("you@example.com");
    fireEvent.change(input, { target: { value: "test@example.com" } });
    fireEvent.click(screen.getByText("Get Early Access"));
    expect(screen.getByText(/on the list/)).toBeInTheDocument();
  });

  it("stores email in localStorage", () => {
    render(<LaunchEmailForm />);
    const input = screen.getByPlaceholderText("you@example.com");
    fireEvent.change(input, { target: { value: "test@example.com" } });
    fireEvent.click(screen.getByText("Get Early Access"));
    const stored = JSON.parse(localStorage.getItem("chartora_launch_emails") ?? "[]");
    expect(stored).toContain("test@example.com");
  });
});
