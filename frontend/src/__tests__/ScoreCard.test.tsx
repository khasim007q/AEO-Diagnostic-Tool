import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ScoreCard from "../components/ScoreCard";
import { SupportingMetrics } from "../lib/types";

describe("ScoreCard Component", () => {
  const mockMetrics: SupportingMetrics = {
    engine_availability: 100.0,
    engine_availability_display: "3/3 engines",
    mention_coverage: 100.0,
    mention_coverage_display: "3/3 (100%)",
    median_rank: 2.0,
    average_rank: 2.0,
    best_rank: 1,
    worst_rank: 3,
    successful_engine_count: 3,
    configured_engine_count: 3,
    mentioned_engine_count: 3,
  };

  it("renders AI Visibility score out of 100 with label and metrics", () => {
    render(
      <ScoreCard
        score={78.0}
        visibilityLabel="High visibility"
        supportingMetrics={mockMetrics}
      />
    );

    expect(screen.getByText("78")).toBeInTheDocument();
    expect(screen.getByText("/ 100")).toBeInTheDocument();
    expect(screen.getByText("High visibility")).toBeInTheDocument();
    expect(screen.getAllByText("3/3 engines").length).toBeGreaterThan(0);
    expect(screen.getByText("3/3 (100%)")).toBeInTheDocument();
    expect(screen.getByText("#2")).toBeInTheDocument();
    expect(screen.getByText("#1 / #3")).toBeInTheDocument();
  });

  it("renders 0 score and Not visible label cleanly", () => {
    const zeroMetrics: SupportingMetrics = {
      engine_availability: 100.0,
      engine_availability_display: "3/3 engines",
      mention_coverage: 0.0,
      mention_coverage_display: "0/3 (0%)",
      median_rank: null,
      average_rank: null,
      best_rank: null,
      worst_rank: null,
      successful_engine_count: 3,
      configured_engine_count: 3,
      mentioned_engine_count: 0,
    };

    render(
      <ScoreCard
        score={0.0}
        visibilityLabel="Not visible"
        supportingMetrics={zeroMetrics}
      />
    );

    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getByText("/ 100")).toBeInTheDocument();
    expect(screen.getByText("Not visible")).toBeInTheDocument();
    expect(screen.getByText("0/3 (0%)")).toBeInTheDocument();
    expect(screen.getByText("None / None")).toBeInTheDocument();
  });
});
