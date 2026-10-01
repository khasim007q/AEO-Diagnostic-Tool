import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ScoreCard from "../components/ScoreCard";
import { GradeResult } from "../lib/types";

describe("ScoreCard Component", () => {
  it("renders Grade A correctly with label and scores", () => {
    const data: GradeResult = {
      grade: "A",
      label: "Excellent AI visibility across all engines",
      score: 42.5,
      max_score: 50.0,
    };
    render(<ScoreCard data={data} />);

    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("Excellent AI visibility across all engines")).toBeInTheDocument();
    expect(screen.getByText("42.5 / 50")).toBeInTheDocument();
  });

  it("renders Grade F for zero score with proper styling", () => {
    const data: GradeResult = {
      grade: "F",
      label: "Not visible to AI engines for this query",
      score: 0.0,
      max_score: 50.0,
    };
    render(<ScoreCard data={data} />);

    expect(screen.getByText("F")).toBeInTheDocument();
    expect(screen.getByText("Not visible to AI engines for this query")).toBeInTheDocument();
    expect(screen.getByText("0 / 50")).toBeInTheDocument();
  });

  it("handles boundary scores properly", () => {
    const data: GradeResult = {
      grade: "C",
      label: "Average visibility, significant gaps exist",
      score: 20.0,
      max_score: 50.0,
    };
    render(<ScoreCard data={data} />);

    expect(screen.getByText("C")).toBeInTheDocument();
    expect(screen.getByText("20 / 50")).toBeInTheDocument();
  });
});
