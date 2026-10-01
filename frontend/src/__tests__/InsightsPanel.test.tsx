import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import InsightsPanel from "../components/InsightsPanel";
import { TypedInsight } from "../lib/types";

describe("InsightsPanel Component", () => {
  it("renders typed insights with titles and messages", () => {
    const mockInsights: TypedInsight[] = [
      {
        type: "positive",
        title: "Category Leader",
        message: "Nike achieved the highest AI Visibility Score of 90.0/100 across evaluated models.",
        evidence: { leader: "Nike", score: 90.0 },
      },
      {
        type: "warning",
        title: "Search Corroboration Gap",
        message: "Nike was recommended by AI models but not observed in top organic Google results.",
        evidence: { brand: "Nike" },
      },
    ];

    render(<InsightsPanel insights={mockInsights} />);

    expect(screen.getByText("Actionable Diagnostic Insights")).toBeInTheDocument();
    expect(screen.getByText("Category Leader")).toBeInTheDocument();
    expect(screen.getByText(/highest AI Visibility Score of 90.0\/100/)).toBeInTheDocument();
    expect(screen.getByText("Search Corroboration Gap")).toBeInTheDocument();
  });

  it("returns null when insights list is empty", () => {
    const { container } = render(<InsightsPanel insights={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
