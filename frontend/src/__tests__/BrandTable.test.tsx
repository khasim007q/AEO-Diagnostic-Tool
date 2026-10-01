import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import BrandTable from "../components/BrandTable";
import { BrandResult, EngineSummary } from "../lib/types";

describe("BrandTable Component", () => {
  const mockEngineSummaries: EngineSummary[] = [
    {
      engine: "GPT-5-mini",
      status: "success",
      latency_ms: 500,
      attempts: 1,
      recommendations_count: 5,
    },
    {
      engine: "Claude Sonnet 4",
      status: "success",
      latency_ms: 600,
      attempts: 1,
      recommendations_count: 5,
    },
  ];

  const mockBrands: BrandResult[] = [
    {
      name: "Nike",
      normalized_name: "nike",
      ai_visibility_score: 90.0,
      visibility_label: "High visibility",
      supporting_metrics: {
        engine_availability: 100.0,
        engine_availability_display: "2/2 engines",
        mention_coverage: 100.0,
        mention_coverage_display: "2/2 (100%)",
        median_rank: 1.5,
        average_rank: 1.5,
        best_rank: 1,
        worst_rank: 2,
        successful_engine_count: 2,
        configured_engine_count: 2,
        mentioned_engine_count: 2,
      },
      observations: {
        "GPT-5-mini": {
          engine: "GPT-5-mini",
          status: "success",
          mentioned: true,
          best_rank: 1,
          position_score: 1.0,
          products: [
            {
              brand_name: "Nike",
              product_name: "Nike Pegasus 40",
              full_name: "Nike Pegasus 40",
              rank: 1,
              engine: "GPT-5-mini",
            },
            {
              brand_name: "Nike",
              product_name: "Nike Vaporfly 3",
              full_name: "Nike Vaporfly 3",
              rank: 4,
              engine: "GPT-5-mini",
            },
          ],
          latency_ms: 500,
        },
        "Claude Sonnet 4": {
          engine: "Claude Sonnet 4",
          status: "success",
          mentioned: true,
          best_rank: 2,
          position_score: 0.8,
          products: [
            {
              brand_name: "Nike",
              product_name: "Nike Pegasus 40",
              full_name: "Nike Pegasus 40",
              rank: 2,
              engine: "Claude Sonnet 4",
            },
          ],
          latency_ms: 600,
        },
      },
      products: [
        {
          brand_name: "Nike",
          product_name: "Nike Pegasus 40",
          full_name: "Nike Pegasus 40",
          rank: 1,
          engine: "GPT-5-mini",
        },
        {
          brand_name: "Nike",
          product_name: "Nike Vaporfly 3",
          full_name: "Nike Vaporfly 3",
          rank: 4,
          engine: "GPT-5-mini",
        },
      ],
    },
  ];

  it("renders brand table with dynamic engine columns and score", () => {
    render(
      <BrandTable
        brands={mockBrands}
        engineSummaries={mockEngineSummaries}
      />
    );

    expect(screen.getByText("Nike")).toBeInTheDocument();
    expect(screen.getByText("90.0 / 100")).toBeInTheDocument();
    expect(screen.getByText("2/2 (100%)")).toBeInTheDocument();
    expect(screen.getByText("GPT-5-mini")).toBeInTheDocument();
    expect(screen.getByText("Claude Sonnet 4")).toBeInTheDocument();
    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.getByText("#2")).toBeInTheDocument();
  });

  it("highlights target brand with Target badge", () => {
    render(
      <BrandTable
        brands={mockBrands}
        targetBrand={mockBrands[0]}
        engineSummaries={mockEngineSummaries}
      />
    );

    expect(screen.getByText("Target")).toBeInTheDocument();
  });

  it("expands product evidence when clicking brand row", () => {
    render(
      <BrandTable
        brands={mockBrands}
        engineSummaries={mockEngineSummaries}
      />
    );

    expect(screen.queryByText("Product Evidence for Nike")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Nike"));

    expect(screen.getByText("Product Evidence for Nike")).toBeInTheDocument();
    expect(screen.getByText("Nike Vaporfly 3")).toBeInTheDocument();
    expect(screen.getByText("#4")).toBeInTheDocument();
  });
});
