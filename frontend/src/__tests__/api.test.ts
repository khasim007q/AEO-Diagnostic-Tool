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

  it("validates realistic multi-engine response with all statuses against Zod schema", async () => {
    const realisticResponse: DiagnosticResponse = {
      metadata: {
        query: "best wireless headphones",
        target_brand: "Sony",
        website_or_domain: "sony.com",
        market: "US",
        timestamp: "2026-10-01T12:00:00Z",
      },
      ai_visibility_score: 80.0,
      visibility_label: "High visibility",
      supporting_metrics: {
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
      },
      target_brand: {
        name: "Sony",
        normalized_name: "sony",
        domain: "sony.com",
        ai_visibility_score: 80.0,
        visibility_label: "High visibility",
        supporting_metrics: {
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
                brand_name: "Sony",
                product_name: "Sony WH-1000XM5",
                full_name: "Sony WH-1000XM5",
                rank: 1,
                engine: "GPT-5-mini",
              },
            ],
            latency_ms: 450,
          },
          "Claude Sonnet 4": {
            engine: "Claude Sonnet 4",
            status: "partial",
            mentioned: true,
            best_rank: 2,
            position_score: 0.0,
            products: [],
            latency_ms: 600,
          },
          "Gemini 2.5 Flash": {
            engine: "Gemini 2.5 Flash",
            status: "failed",
            mentioned: false,
            best_rank: null,
            position_score: 0.0,
            products: [],
            latency_ms: 1200,
            error_type: "timeout",
          },
        },
        products: [
          {
            brand_name: "Sony",
            product_name: "Sony WH-1000XM5",
            full_name: "Sony WH-1000XM5",
            rank: 1,
            engine: "GPT-5-mini",
          },
        ],
      },
      all_brands: [],
      competitors: [],
      engine_summaries: [
        {
          engine: "GPT-5-mini",
          status: "success",
          latency_ms: 450,
          attempts: 1,
          recommendations_count: 5,
        },
        {
          engine: "Claude Sonnet 4",
          status: "partial",
          latency_ms: 600,
          attempts: 1,
          recommendations_count: 3,
        },
        {
          engine: "Gemini 2.5 Flash",
          status: "failed",
          latency_ms: 1200,
          attempts: 2,
          recommendations_count: 0,
          error_type: "timeout",
        },
      ],
      gap_analysis: [
        {
          competitor: "Bose",
          engine: "Overall",
          your_score: 80.0,
          their_score: 60.0,
          gap: 20.0,
          status: "winning",
        },
      ],
      google_corroboration: {
        status: "success",
        total_results: 10,
        brand_found: true,
        best_google_rank: 1,
        results: [
          {
            rank: 1,
            title: "Sony Headphones",
            snippet: "Official Sony site",
            url: "https://www.sony.com",
            domain: "sony.com",
            title_match: true,
            snippet_match: true,
            domain_match: true,
            normalized_brand_match: true,
            match_type: "domain",
            confidence: 1.0,
          },
        ],
      },
      insights: [
        {
          type: "positive",
          title: "Strong AI Presence",
          message: "Sony is ranked #1 in GPT-5-mini.",
          evidence: { score: 80.0 },
        },
      ],
      raw_evidence: {
        "GPT-5-mini": {
          engine: "GPT-5-mini",
          status: "success",
          raw_content: "{}",
          parsed_count: 5,
          latency_ms: 450,
          attempts: 1,
        },
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => realisticResponse,
    });

    const parsed = await runDiagnostic({
      query: "best wireless headphones",
      your_brand: "Sony",
      market: "US",
      language: "en",
      google_domain: "google.com",
    });
    expect(parsed.target_brand?.name).toBe("Sony");
    expect(parsed.target_brand?.observations["Claude Sonnet 4"].status).toBe("partial");
    expect(parsed.target_brand?.observations["Gemini 2.5 Flash"].status).toBe("failed");
    expect(parsed.target_brand?.observations["GPT-5-mini"].status).toBe("success");
    expect(parsed.target_brand?.supporting_metrics.mention_coverage).toBe(100.0);
  });
});
