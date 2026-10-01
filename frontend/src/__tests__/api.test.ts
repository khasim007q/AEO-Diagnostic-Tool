import { describe, it, expect, vi, beforeEach } from "vitest";
import { runDiagnostic, ApiError } from "../lib/api";
import { DiagnosticRequest, DiagnosticResponse } from "../lib/types";

describe("API Client (lib/api.ts)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const validResponse: DiagnosticResponse = {
    metadata: {
      query: "best shoes",
      target_brand: "Nike",
      market: "US",
      timestamp: "2026-10-01T12:00:00Z",
    },
    ai_visibility_score: 90.0,
    visibility_label: "High visibility",
    supporting_metrics: {
      engine_availability: 100.0,
      engine_availability_display: "3/3 engines",
      mention_coverage: 100.0,
      mention_coverage_display: "3/3 (100%)",
      median_rank: 1.0,
      average_rank: 1.0,
      best_rank: 1,
      worst_rank: 1,
      successful_engine_count: 3,
      configured_engine_count: 3,
      mentioned_engine_count: 3,
    },
    target_brand: null,
    all_brands: [],
    competitors: [],
    engine_summaries: [],
    gap_analysis: [],
    google_corroboration: {
      status: "not_configured",
      total_results: 0,
      brand_found: false,
      results: [],
    },
    insights: [],
    raw_evidence: {},
  };

  it("calls /diagnostic endpoint and validates schema on success", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => validResponse,
    });

    const request: DiagnosticRequest = {
      query: "best running shoes",
      your_brand: "Nike",
      market: "US",
      language: "en",
      google_domain: "google.com",
    };
    const result = await runDiagnostic(request);

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result.ai_visibility_score).toBe(90.0);
    expect(result.visibility_label).toBe("High visibility");
  });

  it("throws ApiError with status 429 when rate limited", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => ({ detail: "Rate limit reached" }),
    });

    await expect(
      runDiagnostic({
        query: "best running shoes",
        market: "US",
        language: "en",
        google_domain: "google.com",
      })
    ).rejects.toThrow(ApiError);
  });

  it("throws validation error when backend returns malformed data", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ unexpected: "shape" }),
    });

    await expect(
      runDiagnostic({
        query: "best running shoes",
        market: "US",
        language: "en",
        google_domain: "google.com",
      })
    ).rejects.toThrow(/unexpected response format/);
  });
});
