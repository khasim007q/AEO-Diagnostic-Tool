import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import GapAnalysis from "../components/GapAnalysis";
import { GapEntry } from "../lib/types";

describe("GapAnalysis Component", () => {
  const mockGaps: GapEntry[] = [
    {
      competitor: "Competitor A",
      engine: "Overall",
      your_score: 80.0,
      their_score: 60.0,
      gap: 20.0,
      status: "winning",
    },
    {
      competitor: "Competitor B",
      engine: "Overall",
      your_score: 40.0,
      their_score: 80.0,
      gap: -40.0,
      status: "losing",
    },
    {
      competitor: "Competitor C",
      engine: "Overall",
      your_score: 60.0,
      their_score: 60.0,
      gap: 0.0,
      status: "tied",
    },
  ];

  it("renders competitor gap entries with scores and status badges", () => {
    render(<GapAnalysis gaps={mockGaps} targetBrandName="Nike" />);

    expect(screen.getByText("Competitor A")).toBeInTheDocument();
    expect(screen.getByText("Competitor B")).toBeInTheDocument();
    expect(screen.getByText("Competitor C")).toBeInTheDocument();

    expect(screen.getByText("Leading")).toBeInTheDocument();
    expect(screen.getByText("Trailing")).toBeInTheDocument();
    expect(screen.getByText("Tied")).toBeInTheDocument();
  });

  it("displays signed gap numbers with + and - signs", () => {
    render(<GapAnalysis gaps={mockGaps} targetBrandName="Nike" />);

    expect(screen.getByText("+20.0")).toBeInTheDocument();
    expect(screen.getByText("-40.0")).toBeInTheDocument();
    expect(screen.getByText("0.0")).toBeInTheDocument();
  });
});
