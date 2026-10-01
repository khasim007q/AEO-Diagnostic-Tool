import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import RawResponses from "../components/RawResponses";

describe("RawResponses Component", () => {
  const mockResponses = {
    "GPT-5-mini": {
      raw: '[{"rank": 1, "brand": "BrandA", "product": "ProductA"}]',
      parsed_count: 1,
    },
    "Claude Sonnet": {
      raw: "Here are recommendations:\n1. BrandB ProductB",
      parsed_count: 1,
    },
  };

  it("renders tabs for each model and shows active model response", () => {
    render(<RawResponses responses={mockResponses} />);

    expect(screen.getByText("Raw LLM Responses")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "GPT-5-mini" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Claude Sonnet" })).toBeInTheDocument();

    // Default first tab active
    expect(screen.getByText(/BrandA/)).toBeInTheDocument();

    // Click Claude tab
    fireEvent.click(screen.getByRole("button", { name: "Claude Sonnet" }));
    expect(screen.getByText(/BrandB ProductB/)).toBeInTheDocument();
  });

  it("returns null when no responses provided", () => {
    const { container } = render(<RawResponses responses={{}} />);
    expect(container.firstChild).toBeNull();
  });
});
