import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import GoogleResults from "../components/GoogleResults";
import { GoogleCorroborationSummary } from "../lib/types";

describe("GoogleResults Component", () => {
  it("renders Google search corroboration results with match badges", () => {
    const mockSummary: GoogleCorroborationSummary = {
      status: "success",
      total_results: 2,
      brand_found: true,
      best_google_rank: 1,
      results: [
        {
          rank: 1,
          title: "Nike Official Store - Running Shoes",
          snippet: "Shop Nike running shoes and apparel.",
          url: "https://www.nike.com/running",
          domain: "nike.com",
          title_match: true,
          snippet_match: true,
          domain_match: true,
          normalized_brand_match: true,
          match_type: "domain",
          confidence: 1.0,
        },
        {
          rank: 2,
          title: "Best Marathon Shoes Comparison",
          snippet: "Top running shoes reviewed.",
          url: "https://runnersworld.com/marathon",
          domain: "runnersworld.com",
          title_match: false,
          snippet_match: false,
          domain_match: false,
          normalized_brand_match: false,
          match_type: "none",
          confidence: 0.0,
        },
      ],
    };

    render(<GoogleResults summary={mockSummary} targetBrandName="Nike" />);

    expect(screen.getByText("Google Search Corroboration")).toBeInTheDocument();
    expect(screen.getByText("Found at Organic #1")).toBeInTheDocument();
    expect(screen.getByText("Nike Official Store - Running Shoes")).toBeInTheDocument();
    expect(screen.getByText("Domain Match (100%)")).toBeInTheDocument();
    expect(screen.getByText("Organic Competitor")).toBeInTheDocument();
  });

  it("renders not_configured state cleanly", () => {
    const mockSummary: GoogleCorroborationSummary = {
      status: "not_configured",
      total_results: 0,
      brand_found: false,
      results: [],
    };

    render(<GoogleResults summary={mockSummary} />);

    expect(screen.getByText("Search Corroboration Not Configured")).toBeInTheDocument();
  });

  it("renders failed state cleanly with error message", () => {
    const mockSummary: GoogleCorroborationSummary = {
      status: "failed",
      error_message: "Rate limit reached on SerpApi",
      total_results: 0,
      brand_found: false,
      results: [],
    };

    render(<GoogleResults summary={mockSummary} />);

    expect(screen.getByText("Search Corroboration Engine Unavailable")).toBeInTheDocument();
    expect(screen.getByText("Rate limit reached on SerpApi")).toBeInTheDocument();
  });
});
