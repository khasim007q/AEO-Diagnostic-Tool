import { describe, it, expect, vi, beforeEach } from "vitest";
import { runDiagnostic } from "../lib/api";
import { DiagnosticRequest, DiagnosticResponse } from "../lib/types";

describe("API Client (lib/api.ts)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("calls /diagnostic endpoint and parses JSON on success", async () => {
    const mockResponse: Partial<DiagnosticResponse> = {
      grade: { grade: "A", label: "Excellent", score: 40, max_score: 50 },
      all_brands: [],
      insights: ["Test insight"],
      google_results: [],
      raw_llm_responses: {},
      llm_names: ["GPT-5-mini"],
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const request: DiagnosticRequest = { query: "best shoes", your_brand: "Nike" };
    const result = await runDiagnostic(request);

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result.grade.grade).toBe("A");
  });

  it("throws formatted error message on API failure", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "Query must be at least 3 characters" }),
    });

    await expect(runDiagnostic({ query: "a" })).rejects.toThrow("Query must be at least 3 characters");
  });

  it("handles non-JSON error response gracefully", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => {
        throw new Error("Invalid JSON");
      },
    });

    await expect(runDiagnostic({ query: "valid" })).rejects.toThrow("Failed to run diagnostic");
  });
});
