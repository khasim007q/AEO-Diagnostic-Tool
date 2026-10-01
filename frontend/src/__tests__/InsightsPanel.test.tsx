import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import InsightsPanel from "../components/InsightsPanel";

describe("InsightsPanel Component", () => {
  it("renders positive, negative, and informational insights", () => {
    const insights = [
      "The top performing brand is BrandX with a total score of 45.0.",
      "BrandY does not appear in top Google results for this query.",
      "You outscore your nearest competitor by 12.0 points.",
    ];

    render(<InsightsPanel insights={insights} />);

    expect(screen.getByText("Actionable Insights")).toBeInTheDocument();
    expect(screen.getByText(/The top performing brand is BrandX/)).toBeInTheDocument();
    expect(screen.getByText(/BrandY does not appear in top Google results/)).toBeInTheDocument();
    expect(screen.getByText(/You outscore your nearest competitor/)).toBeInTheDocument();
  });
});
