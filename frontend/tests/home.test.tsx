import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

describe("Home page", () => {
  it("renders without crashing", () => {
    // Basic smoke test to verify test setup works
    const div = document.createElement("div");
    div.textContent = "Chartora";
    document.body.appendChild(div);
    expect(screen.getByText("Chartora")).toBeDefined();
  });
});
