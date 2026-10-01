export interface DiagnosticRequest {
  query: string;
  your_brand?: string;
}

export interface ProductResult {
  brand_name: string;
  product_name: string;
  full_name: string;
  ranks: Record<string, number>;
  score: number;
  web_validated: boolean;
  web_rank: number | null;
}

export interface BrandResult {
  name: string;
  products: ProductResult[];
  total_score: number;
  llm_coverage: string[];
  consensus_pct: number;
}

export interface GradeResult {
  grade: string;
  label: string;
  score: number;
  max_score: number;
}

export interface GapEntry {
  competitor: string;
  llm: string;
  your_score: number;
  their_score: number;
  gap: number;
  status: 'winning' | 'tied' | 'losing';
}

export interface GoogleResult {
  rank: number;
  title: string;
  snippet: string;
  url: string;
}

export interface DiagnosticResponse {
  grade: GradeResult;
  your_brand: BrandResult | null;
  all_brands: BrandResult[];
  competitors: BrandResult[];
  gap_analysis: GapEntry[];
  insights: string[];
  google_results: GoogleResult[];
  raw_llm_responses: Record<string, { raw: string; parsed_count: number }>;
  llm_names: string[];
}
