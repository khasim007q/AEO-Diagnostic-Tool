import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import BrandTable from "../components/BrandTable";
import { BrandResult } from "../lib/types";

describe("BrandTable Component", () => {
  const mockBrands: BrandResult[] = [
    {
      name: "Optimum Nutrition",
      total_score: 39.0,
      consensus_pct: 100,
      llm_coverage: ["GPT-5-mini", "Claude Sonnet", "Gemini 2.5 Flash"],
      products: [
        {
          brand_name: "Optimum Nutrition",
          product_name: "Gold Standard 100% Whey",
          full_name: "Optimum Nutrition Gold Standard 100% Whey",
          ranks: { "GPT-5-mini": 1, "Claude Sonnet": 1, "Gemini 2.5 Flash": 1 },
          score: 39.0,
          web_validated: true,
          web_rank: 1,
        },
      ],
    },
    {
      name: "Dymatize",
      total_score: 23.4,
      consensus_pct: 66.7,
      llm_coverage: ["GPT-5-mini", "Gemini 2.5 Flash"],
      products: [
        {
          brand_name: "Dymatize",
          product_name: "ISO100 Hydrolyzed",
          full_name: "Dymatize ISO100 Hydrolyzed",
          ranks: { "GPT-5-mini": 2, "Gemini 2.5 Flash": 2 },
          score: 23.4,
          web_validated: false,
          web_rank: null,
        },
      ],
    },
  ];

  it("renders brands table with correct score and consensus", () => {
    render(<BrandTable brands={mockBrands} yourBrand={null} />);

    expect(screen.getByText("Optimum Nutrition")).toBeInTheDocument();
    expect(screen.getByText("Dymatize")).toBeInTheDocument();
    expect(screen.getByText("39")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("highlights user brand with a special badge", () => {
    render(<BrandTable brands={mockBrands} yourBrand={mockBrands[0]} />);

    expect(screen.getByText("Your Brand")).toBeInTheDocument();
  });

  it("expands product details when brand row is clicked", () => {
    render(<BrandTable brands={mockBrands} yourBrand={null} />);

    // Initially products are not expanded
    expect(screen.queryByText("Gold Standard 100% Whey")).not.toBeInTheDocument();

    // Click brand row to expand
    fireEvent.click(screen.getByText("Optimum Nutrition"));

    // Now product is visible
    expect(screen.getByText("Gold Standard 100% Whey")).toBeInTheDocument();
    expect(screen.getAllByText("#1").length).toBeGreaterThan(0);
  });
});
