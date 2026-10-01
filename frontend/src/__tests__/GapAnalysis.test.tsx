import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import GapAnalysis from "../components/GapAnalysis";
import { GapEntry } from "../lib/types";

describe("GapAnalysis Component", () => {
  const mockGaps: GapEntry[] = [
    {
      competitor: "Competitor A",
      llm: "GPT-5-mini",
      your_score: 10.0,
      their_score: 6.0,
      gap: 4.0,
      status: "winning",
    },
    {
      competitor: "Competitor B",
      llm: "Claude Sonnet",
      your_score: 4.0,
      their_score: 10.0,
      gap: -6.0,
      status: "losing",
    },
    {
      competitor: "Competitor C",
      llm: "Gemini 2.5 Flash",
      your_score: 6.0,
      their_score: 6.0,
      gap: 0.0,
      status: "tied",
    },
  ];

  it("renders competitor gap entries with scores and status badges", () => {
    render(<GapAnalysis gaps={mockGaps} />);

    expect(screen.getByText("Competitor A")).toBeInTheDocument();
    expect(screen.getByText("Competitor B")).toBeInTheDocument();
    expect(screen.getByText("Competitor C")).toBeInTheDocument();

    expect(screen.getByText("Winning")).toBeInTheDocument();
    expect(screen.getByText("Losing")).toBeInTheDocument();
    expect(screen.getByText("Tied")).toBeInTheDocument();
  });

  it("displays gap numbers accurately", () => {
    render(<GapAnalysis gaps={mockGaps} />);

    expect(screen.getByText("+4")).toBeInTheDocument();
    expect(screen.getByText("-6")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
  });
});
