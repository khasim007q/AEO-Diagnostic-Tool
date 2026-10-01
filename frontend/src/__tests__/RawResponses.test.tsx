import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import RawResponses from "../components/RawResponses";
import { RawEvidence } from "../lib/types";

describe("RawResponses Component", () => {
  const mockEvidence: Record<string, RawEvidence> = {
    "GPT-5-mini": {
      engine: "GPT-5-mini",
      status: "success",
      raw_content: '{"recommendations": [{"rank": 1, "brand": "BrandA", "product": "ProductA"}]}',
      parsed_count: 1,
      latency_ms: 450,
      attempts: 1,
    },
    "Claude Sonnet 4": {
      engine: "Claude Sonnet 4",
      status: "failed",
      raw_content: "",
      parsed_count: 0,
      latency_ms: 12000,
      attempts: 3,
      error: "Timeout after 3 retries",
    },
  };

  it("renders tabs for each model and shows active model response and telemetry", () => {
    render(<RawResponses evidence={mockEvidence} />);

    expect(screen.getByText("Raw Engine Evidence and Telemetry")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /GPT-5-mini/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Claude Sonnet 4/ })).toBeInTheDocument();

    // Default first tab active
    expect(screen.getByText(/BrandA/)).toBeInTheDocument();
    expect(screen.getByText("450 ms")).toBeInTheDocument();
    expect(screen.getByText("1 attempt")).toBeInTheDocument();

    // Click Claude tab
    fireEvent.click(screen.getByRole("button", { name: /Claude Sonnet 4/ }));
    expect(screen.getByText("Timeout after 3 retries")).toBeInTheDocument();
    expect(screen.getByText("12000 ms")).toBeInTheDocument();
    expect(screen.getByText("3 attempts")).toBeInTheDocument();
  });

  it("returns null when no evidence provided", () => {
    const { container } = render(<RawResponses evidence={{}} />);
    expect(container.firstChild).toBeNull();
  });
});
