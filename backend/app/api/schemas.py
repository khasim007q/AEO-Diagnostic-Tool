# schemas.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class DiagnosticRequest(BaseModel):
    """Request payload for running an AI Visibility Diagnostic."""
    query: str = Field(..., min_length=3, max_length=300, description="Product query or evaluation question")
    your_brand: Optional[str] = Field(None, max_length=100, description="Optional target brand for gap analysis")
    website_or_domain: Optional[str] = Field(None, max_length=200, description="Optional domain or website for target brand")
    market: Optional[str] = Field("US", description="Search market preset (US, UK, India, Canada, Australia, Germany)")
    location: Optional[str] = Field(None, max_length=100, description="Optional specific location for search")
    language: Optional[str] = Field(None, max_length=20, description="Optional language code")
    google_domain: Optional[str] = Field(None, max_length=50, description="Optional Google domain")


class ProductEvidenceSchema(BaseModel):
    """Evidence record for a product returned by an engine."""
    brand_name: str
    product_name: str
    full_name: str
    rank: int
    engine: str


class EngineObservationSchema(BaseModel):
    """Scoring observation for a brand within a specific engine run."""
    engine: str
    status: str  # "success" | "failed" | "invalid"
    mentioned: bool
    best_rank: Optional[int] = None
    position_score: float
    products: List[ProductEvidenceSchema] = Field(default_factory=list)
    latency_ms: float = 0.0
    error_type: Optional[str] = None


class SupportingMetricsSchema(BaseModel):
    """Explicit supporting metrics with distinct denominators."""
    engine_availability: float  # Percentage (e.g. 100.0 or 66.7)
    engine_availability_display: str  # "3/3 engines"
    mention_coverage: float  # Percentage (e.g. 100.0 or 50.0)
    mention_coverage_display: str  # "2/2 (100%)"
    median_rank: Optional[float] = None
    average_rank: Optional[float] = None
    best_rank: Optional[int] = None
    worst_rank: Optional[int] = None
    successful_engine_count: int
    configured_engine_count: int
    mentioned_engine_count: int


class BrandResultSchema(BaseModel):
    """Ranked brand entity containing metrics and product evidence."""
    name: str
    normalized_name: str
    ai_visibility_score: float  # 0 to 100
    visibility_label: str  # "High visibility", "Moderate visibility", etc.
    metrics: SupportingMetricsSchema
    engine_observations: Dict[str, EngineObservationSchema] = Field(default_factory=dict)
    products: List[ProductEvidenceSchema] = Field(default_factory=list)


class EngineSummarySchema(BaseModel):
    """High-level summary of an engine's execution status."""
    engine: str
    status: str  # "success" | "failed" | "invalid"
    latency_ms: float
    attempts: int
    recommendations_count: int
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class GoogleCorroborationResultSchema(BaseModel):
    """Individual organic Google search result evaluated independently."""
    rank: int
    title: str
    snippet: str
    url: str
    domain: str
    title_match: bool
    snippet_match: bool
    domain_match: bool
    normalized_brand_match: bool
    match_type: str  # "domain" | "title" | "snippet" | "none"
    confidence: float


class GoogleCorroborationSummarySchema(BaseModel):
    """Summary of Google organic search presence as an independent signal."""
    status: str  # "success" | "not_configured" | "failed"
    error_message: Optional[str] = None
    total_results: int = 0
    brand_found: bool = False
    best_google_rank: Optional[int] = None
    results: List[GoogleCorroborationResultSchema] = Field(default_factory=list)


class GapEntrySchema(BaseModel):
    """Signed head-to-head gap analysis entry."""
    competitor: str
    engine: str  # "Overall" or engine name
    your_score: float
    their_score: float
    gap: float  # your_score - their_score (positive = winning, negative = losing)
    status: str  # "winning" | "losing" | "tied"


class TypedInsightSchema(BaseModel):
    """Factual, evidence-based insight object without causal claims."""
    type: str  # "positive" | "warning" | "info"
    title: str
    message: str
    evidence: Dict[str, Any] = Field(default_factory=dict)


class RequestMetadataSchema(BaseModel):
    """Metadata regarding the executed diagnostic."""
    query: str
    target_brand: Optional[str] = None
    website_or_domain: Optional[str] = None
    market: str
    timestamp: str


class RawEvidenceSchema(BaseModel):
    """Raw LLM response details for audit and inspection."""
    engine: str
    status: str
    raw_content: str
    parsed_count: int
    latency_ms: float
    attempts: int
    error: Optional[str] = None


class DiagnosticResponse(BaseModel):
    """Comprehensive, self-contained AI Visibility Diagnostic response."""
    metadata: RequestMetadataSchema
    ai_visibility_score: float  # 0 to 100
    visibility_label: str
    supporting_metrics: SupportingMetricsSchema
    target_brand: Optional[BrandResultSchema] = None
    all_brands: List[BrandResultSchema] = Field(default_factory=list)
    competitors: List[BrandResultSchema] = Field(default_factory=list)
    engine_summaries: List[EngineSummarySchema] = Field(default_factory=list)
    gap_analysis: List[GapEntrySchema] = Field(default_factory=list)
    google_corroboration: GoogleCorroborationSummarySchema
    insights: List[TypedInsightSchema] = Field(default_factory=list)
    raw_evidence: Dict[str, RawEvidenceSchema] = Field(default_factory=dict)
