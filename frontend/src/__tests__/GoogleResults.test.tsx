import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import GoogleResults from "../components/GoogleResults";
import { GoogleResult } from "../lib/types";

describe("GoogleResults Component", () => {
  const mockResults: GoogleResult[] = [
    {
      rank: 1,
      title: "Top Rated Running Shoes 2024",
      snippet: "Comprehensive guide to the best running shoes on the market.",
      url: "https://example.com/shoes",
    },
    {
      rank: 2,
      title: "Nike vs Adidas Comparison",
      snippet: "Which shoe brand is better for endurance runners?",
      url: "https://example.com/comparison",
    },
  ];

  it("renders Google search organic results with rank badges and links", () => {
    render(<GoogleResults results={mockResults} />);

    expect(screen.getByText("Google Search Results")).toBeInTheDocument();
    expect(screen.getByText("Top Rated Running Shoes 2024")).toBeInTheDocument();
    expect(screen.getByText("Nike vs Adidas Comparison")).toBeInTheDocument();
    expect(screen.getByText("https://example.com/shoes")).toBeInTheDocument();
  });

  it("renders empty state without crashing if results are empty", () => {
    render(<GoogleResults results={[]} />);

    expect(screen.getByText("Google Search Results")).toBeInTheDocument();
  });
});
