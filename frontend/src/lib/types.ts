// types.ts
import { z } from "zod";

export const DiagnosticRequestSchema = z.object({
  query: z.string().min(3).max(500),
  your_brand: z.string().max(100).optional(),
  website_or_domain: z.string().max(200).optional(),
  market: z.string().default("US"),
  location: z.string().optional(),
  language: z.string().default("en"),
  google_domain: z.string().default("google.com"),
});
export type DiagnosticRequest = z.infer<typeof DiagnosticRequestSchema>;

export const ProductEvidenceSchema = z.object({
  brand_name: z.string(),
  product_name: z.string(),
  full_name: z.string(),
  rank: z.number(),
  engine: z.string(),
});
export type ProductEvidence = z.infer<typeof ProductEvidenceSchema>;

export const EngineObservationSchema = z.object({
  engine: z.string(),
  status: z.enum(["success", "partial", "invalid", "failed"]),
  mentioned: z.boolean(),
  best_rank: z.number().nullable().optional(),
  position_score: z.number(),
  products: z.array(ProductEvidenceSchema).default([]),
  latency_ms: z.number().default(0),
  error_type: z.string().nullable().optional(),
});
export type EngineObservation = z.infer<typeof EngineObservationSchema>;

export const SupportingMetricsSchema = z.object({
  engine_availability: z.number(),
  engine_availability_display: z.string(),
  mention_coverage: z.number(),
  mention_coverage_display: z.string(),
  median_rank: z.number().nullable().optional(),
  average_rank: z.number().nullable().optional(),
  best_rank: z.number().nullable().optional(),
  worst_rank: z.number().nullable().optional(),
  successful_engine_count: z.number(),
  configured_engine_count: z.number(),
  mentioned_engine_count: z.number(),
});
export type SupportingMetrics = z.infer<typeof SupportingMetricsSchema>;

export const BrandResultSchema = z.object({
  name: z.string(),
  normalized_name: z.string(),
  domain: z.string().nullable().optional(),
  ai_visibility_score: z.number(),
  visibility_label: z.string(),
  supporting_metrics: SupportingMetricsSchema,
  observations: z.record(z.string(), EngineObservationSchema).default({}),
  products: z.array(ProductEvidenceSchema).default([]),
});
export type BrandResult = z.infer<typeof BrandResultSchema>;

export const EngineSummarySchema = z.object({
  engine: z.string(),
  status: z.string(),
  latency_ms: z.number(),
  attempts: z.number(),
  recommendations_count: z.number(),
  error_type: z.string().nullable().optional(),
  error_message: z.string().nullable().optional(),
});
export type EngineSummary = z.infer<typeof EngineSummarySchema>;

export const GoogleCorroborationResultSchema = z.object({
  rank: z.number(),
  title: z.string(),
  snippet: z.string(),
  url: z.string(),
  domain: z.string(),
  title_match: z.boolean(),
  snippet_match: z.boolean(),
  domain_match: z.boolean(),
  normalized_brand_match: z.boolean(),
  match_type: z.string(),
  confidence: z.number(),
});
export type GoogleCorroborationResult = z.infer<typeof GoogleCorroborationResultSchema>;

export const GoogleCorroborationSummarySchema = z.object({
  status: z.enum(["success", "not_configured", "failed"]),
  error_message: z.string().nullable().optional(),
  total_results: z.number().default(0),
  brand_found: z.boolean().default(false),
  best_google_rank: z.number().nullable().optional(),
  results: z.array(GoogleCorroborationResultSchema).default([]),
});
export type GoogleCorroborationSummary = z.infer<typeof GoogleCorroborationSummarySchema>;

export const GapEntrySchema = z.object({
  competitor: z.string(),
  engine: z.string(),
  your_score: z.number(),
  their_score: z.number(),
  gap: z.number(),
  status: z.enum(["winning", "losing", "tied"]),
});
export type GapEntry = z.infer<typeof GapEntrySchema>;

export const TypedInsightSchema = z.object({
  type: z.enum(["positive", "warning", "info"]),
  title: z.string(),
  message: z.string(),
  evidence: z.record(z.string(), z.any()).default({}),
});
export type TypedInsight = z.infer<typeof TypedInsightSchema>;

export const RequestMetadataSchema = z.object({
  query: z.string(),
  target_brand: z.string().nullable().optional(),
  website_or_domain: z.string().nullable().optional(),
  market: z.string(),
  timestamp: z.string(),
});
export type RequestMetadata = z.infer<typeof RequestMetadataSchema>;

export const RawEvidenceSchema = z.object({
  engine: z.string(),
  status: z.string(),
  raw_content: z.string(),
  parsed_count: z.number(),
  latency_ms: z.number(),
  attempts: z.number(),
  error: z.string().nullable().optional(),
});
export type RawEvidence = z.infer<typeof RawEvidenceSchema>;

export const DiagnosticResponseSchema = z.object({
  metadata: RequestMetadataSchema,
  ai_visibility_score: z.number(),
  visibility_label: z.string(),
  supporting_metrics: SupportingMetricsSchema,
  target_brand: BrandResultSchema.nullable().optional(),
  all_brands: z.array(BrandResultSchema).default([]),
  competitors: z.array(BrandResultSchema).default([]),
  engine_summaries: z.array(EngineSummarySchema).default([]),
  gap_analysis: z.array(GapEntrySchema).default([]),
  google_corroboration: GoogleCorroborationSummarySchema,
  insights: z.array(TypedInsightSchema).default([]),
  raw_evidence: z.record(z.string(), RawEvidenceSchema).default({}),
});
export type DiagnosticResponse = z.infer<typeof DiagnosticResponseSchema>;
