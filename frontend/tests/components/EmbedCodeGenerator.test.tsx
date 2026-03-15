import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { EmbedCodeGenerator } from "@/components/sharing/EmbedCodeGenerator";

describe("EmbedCodeGenerator", () => {
  const defaultProps = {
    chartUrl: "https://chartora.com/rankings/patents?embed=true",
    title: "Patent Rankings",
  };

  it("renders embed heading", () => {
    render(<EmbedCodeGenerator {...defaultProps} />);
    expect(screen.getByText("Embed this chart")).toBeInTheDocument();
  });

  it("renders textarea with embed code", () => {
    render(<EmbedCodeGenerator {...defaultProps} />);
    const textarea = screen.getByDisplayValue(/<iframe/) as HTMLTextAreaElement;
    expect(textarea).toBeInTheDocument();
    expect(textarea.value).toContain("<iframe");
    expect(textarea.value).toContain(defaultProps.chartUrl);
  });

  it("renders copy button", () => {
    render(<EmbedCodeGenerator {...defaultProps} />);
    expect(screen.getByText("Copy")).toBeInTheDocument();
  });

  it("renders width and height inputs", () => {
    render(<EmbedCodeGenerator {...defaultProps} />);
    expect(screen.getByText("Width")).toBeInTheDocument();
    expect(screen.getByText("Height")).toBeInTheDocument();
  });

  it("uses custom initial dimensions", () => {
    render(
      <EmbedCodeGenerator {...defaultProps} width={800} height={500} />,
    );
    const textarea = screen.getByDisplayValue(/width="800"/) as HTMLTextAreaElement;
    expect(textarea.value).toContain('width="800"');
    expect(textarea.value).toContain('height="500"');
  });

  it("updates embed code when dimensions change", () => {
    render(<EmbedCodeGenerator {...defaultProps} />);
    const widthInput = screen.getByDisplayValue("600");
    fireEvent.change(widthInput, { target: { value: "900" } });
    const textarea = screen.getByDisplayValue(/width="900"/) as HTMLTextAreaElement;
    expect(textarea.value).toContain('width="900"');
  });
});
