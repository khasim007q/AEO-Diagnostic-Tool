from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class DiagnosticRequest(BaseModel):
    """Request model for diagnostic."""
    query: str = Field(..., min_length=3, max_length=500)
    your_brand: Optional[str] = Field(None, max_length=100)

class ProductResult(BaseModel):
    """Result for a specific product."""
    brand_name: str
    product_name: str
    full_name: str
    ranks: Dict[str, int]
    score: float
    web_validated: bool
    web_rank: Optional[int]

class BrandResult(BaseModel):
    """Result for a brand grouping products."""
    name: str
    products: List[ProductResult]
    total_score: float
    llm_coverage: List[str]
    consensus_pct: float

class GradeResult(BaseModel):
    """Grade assigned to a brand."""
    grade: str
    label: str
    score: float
    max_score: float

class GapEntry(BaseModel):
    """Gap analysis entry against a competitor."""
    competitor: str
    llm: str
    your_score: float
    their_score: float
    gap: float
    status: str

class GoogleResult(BaseModel):
    """Result from Google Search."""
    rank: int
    title: str
    snippet: str
    url: str

class DiagnosticResponse(BaseModel):
    """Response model for diagnostic."""
    grade: GradeResult
    your_brand: Optional[BrandResult]
    all_brands: List[BrandResult]
    competitors: List[BrandResult]
    gap_analysis: List[GapEntry]
    insights: List[str]
    google_results: List[GoogleResult]
    raw_llm_responses: Dict[str, dict]
    llm_names: List[str]
